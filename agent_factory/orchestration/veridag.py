"""
VeriDAG: Deterministic Cryptographic Merkle State Engine for Agent Workflows.

Folded in from Veridag (Hardonian/veridag):
- Cryptographic state transitions across multi-agent workflows
- Input & Output SHA-256 hashing
- Merkle-DAG state verification proofs
- Zero-Trust Replay Verification (validates past runs without re-invoking models)
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class VeriDAGNodeProof:
    """Cryptographic attestation of a discrete step execution in the workflow."""
    node_id: str
    executor_id: str
    parent_hashes: list[str]
    input_hash: str
    output_hash: str
    state_merkle_hash: str
    execution_time: float
    output_data: Any


@dataclass
class VeriDAGExecutionProof:
    """Complete cryptographic proof bundle for an entire DAG workflow execution."""
    execution_id: str
    workflow_name: str
    final_merkle_root: str
    node_proofs: dict[str, VeriDAGNodeProof]
    timestamp: float
    is_valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert proof bundle to JSON-serializable dictionary."""
        return {
            "execution_id": self.execution_id,
            "workflow_name": self.workflow_name,
            "final_merkle_root": self.final_merkle_root,
            "timestamp": self.timestamp,
            "is_valid": self.is_valid,
            "node_count": len(self.node_proofs),
            "node_proofs": {
                k: {
                    "node_id": v.node_id,
                    "executor_id": v.executor_id,
                    "parent_hashes": v.parent_hashes,
                    "input_hash": v.input_hash,
                    "output_hash": v.output_hash,
                    "state_merkle_hash": v.state_merkle_hash,
                    "execution_time": v.execution_time,
                }
                for k, v in self.node_proofs.items()
            },
        }


class VeriDAGEngine:
    """
    Executes DAG workflows with cryptographic state chaining and generates
    tamper-evident execution proofs.
    """

    @staticmethod
    def hash_payload(payload: Any) -> str:
        """Deterministically serialize and hash data."""
        try:
            raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        except (TypeError, ValueError, AttributeError):
            raw = str(payload).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @classmethod
    def compute_node_merkle_hash(
        cls,
        node_id: str,
        input_hash: str,
        output_hash: str,
        parent_hashes: list[str],
    ) -> str:
        """
        Compute Merkle node hash:
        H(node_id || input_hash || output_hash || sorted(parent_hashes))
        """
        combined = f"{node_id}:{input_hash}:{output_hash}:{':'.join(sorted(parent_hashes))}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @classmethod
    def execute_verifiable_dag(
        cls,
        workflow_name: str,
        nodes: dict[str, dict[str, Any]],  # node_id -> {fn, parents}
        initial_input: dict[str, Any],
    ) -> tuple[dict[str, Any], VeriDAGExecutionProof]:
        """
        Execute DAG nodes in topological dependency order while calculating
        cryptographic state proofs at every node transition.
        """
        execution_id = f"veridag-{uuid.uuid4().hex[:12]}"
        results: dict[str, Any] = {}
        node_proofs: dict[str, VeriDAGNodeProof] = {}

        # Topological sorting
        executed: set[str] = set()
        pending = set(nodes.keys())

        while pending:
            progress = False
            for node_id in sorted(pending):
                node_spec = nodes[node_id]
                parents: list[str] = node_spec.get("parents", [])

                if all(p in executed for p in parents):
                    # Gather inputs from parents
                    node_inputs = {
                        p: results[p] for p in parents
                    } if parents else dict(initial_input)

                    fn: Callable = node_spec["fn"]
                    start = time.perf_counter()
                    output = fn(node_inputs)
                    duration = time.perf_counter() - start

                    # Compute cryptographic hashes
                    in_hash = cls.hash_payload(node_inputs)
                    out_hash = cls.hash_payload(output)
                    parent_merkle_hashes = [
                        node_proofs[p].state_merkle_hash for p in parents
                    ]
                    node_merkle = cls.compute_node_merkle_hash(
                        node_id=node_id,
                        input_hash=in_hash,
                        output_hash=out_hash,
                        parent_hashes=parent_merkle_hashes,
                    )

                    proof = VeriDAGNodeProof(
                        node_id=node_id,
                        executor_id=node_spec.get("executor_id", "agent"),
                        parent_hashes=parent_merkle_hashes,
                        input_hash=in_hash,
                        output_hash=out_hash,
                        state_merkle_hash=node_merkle,
                        execution_time=duration,
                        output_data=output,
                    )
                    node_proofs[node_id] = proof
                    results[node_id] = output

                    executed.add(node_id)
                    pending.remove(node_id)
                    progress = True
                    break

            if not progress:
                raise ValueError("Cyclic dependency detected in VeriDAG specification.")

        # Compute final workflow Merkle root
        all_node_merkle_hashes = [p.state_merkle_hash for p in node_proofs.values()]
        final_root = hashlib.sha256(
            ":".join(sorted(all_node_merkle_hashes)).encode("utf-8")
        ).hexdigest()

        proof_bundle = VeriDAGExecutionProof(
            execution_id=execution_id,
            workflow_name=workflow_name,
            final_merkle_root=final_root,
            node_proofs=node_proofs,
            timestamp=time.time(),
            is_valid=True,
        )

        return results, proof_bundle

    @classmethod
    def verify_proof(cls, proof: VeriDAGExecutionProof) -> bool:
        """
        Verify that all state transitions in the proof bundle match their Merkle hashes
        and that the final root is mathematically sound.
        """
        try:
            for node_id, node_proof in proof.node_proofs.items():
                expected_merkle = cls.compute_node_merkle_hash(
                    node_id=node_id,
                    input_hash=node_proof.input_hash,
                    output_hash=node_proof.output_hash,
                    parent_hashes=node_proof.parent_hashes,
                )
                if node_proof.state_merkle_hash != expected_merkle:
                    return False

            all_hashes = [p.state_merkle_hash for p in proof.node_proofs.values()]
            expected_final_root = hashlib.sha256(
                ":".join(sorted(all_hashes)).encode("utf-8")
            ).hexdigest()

            return proof.final_merkle_root == expected_final_root
        except Exception:  # noqa: BLE001
            return False
