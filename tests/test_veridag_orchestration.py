"""
Tests for VeriDAG cryptographic state DAG engine.
"""

import pytest

from agent_factory.orchestration.veridag import (
    VeriDAGEngine,
)


@pytest.mark.unit
def test_veridag_execution_and_cryptographic_proof():
    """Verify VeriDAG runs dependency graph and computes tamper-evident Merkle roots."""
    nodes = {
        "step_a": {
            "fn": lambda inp: {"val": inp["base"] * 2},
            "parents": [],
            "executor_id": "math_worker",
        },
        "step_b": {
            "fn": lambda inp: {"val": inp["step_a"]["val"] + 10},
            "parents": ["step_a"],
            "executor_id": "adder_worker",
        },
        "step_c": {
            "fn": lambda inp: {"final": f"Result is {inp['step_b']['val']}"},
            "parents": ["step_b"],
            "executor_id": "formatter_worker",
        },
    }

    results, proof = VeriDAGEngine.execute_verifiable_dag(
        workflow_name="ArithmeticPipeline",
        nodes=nodes,
        initial_input={"base": 5},
    )

    assert results["step_c"]["final"] == "Result is 20"
    assert len(proof.node_proofs) == 3
    assert len(proof.final_merkle_root) == 64

    # Verify cryptographic proof mathematically
    assert VeriDAGEngine.verify_proof(proof) is True

    # Tamper with an intermediate node hash -> verification must fail
    proof.node_proofs["step_b"].output_hash = "tampered_hash_0000000000000000"
    assert VeriDAGEngine.verify_proof(proof) is False
