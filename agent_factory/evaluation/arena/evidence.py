"""Portable signed Arena evidence manifests and offline verification."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_factory import __version__
from agent_factory.orchestration.veridag import VeriDAGEngine


@dataclass(frozen=True)
class VerificationReport:
    valid: bool
    checks: dict[str, bool]
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "checks": self.checks, "errors": self.errors}


class EvidenceSigner:
    """Create portable manifests using HMAC-SHA256 or checksum-only offline mode."""

    def __init__(self, key: str | None = None) -> None:
        configured = key or os.getenv("ARENA_EVIDENCE_SIGNING_KEY")
        self.key = configured.encode("utf-8") if configured else None

    def build_manifest(
        self,
        run_id: str,
        proof_path: Path,
        pcap_path: Path,
        *,
        benchmark_version: str = "2026.10",
        image_digest: str | None = None,
    ) -> dict[str, Any]:
        manifest: dict[str, Any] = {
            "manifest_version": "1.0",
            "run_id": run_id,
            "benchmark_version": benchmark_version,
            "agent_factory_version": __version__,
            "container_image_digest": image_digest or os.getenv("CONTAINER_IMAGE_DIGEST", "unknown"),
            "artifacts": {
                "veridag": {"file": proof_path.name, "sha256": self._file_hash(proof_path)},
                "apcap": {"file": pcap_path.name, "sha256": self._file_hash(pcap_path)},
            },
        }
        canonical = self._canonical(manifest)
        if self.key:
            signature = hmac.new(self.key, canonical, hashlib.sha256).hexdigest()
            manifest["signature"] = {"algorithm": "hmac-sha256", "value": signature}
        else:
            manifest["signature"] = {
                "algorithm": "sha256",
                "value": hashlib.sha256(canonical).hexdigest(),
            }
        return manifest

    def verify_signature(self, manifest: dict[str, Any]) -> bool:
        unsigned = dict(manifest)
        signature = unsigned.pop("signature", {})
        canonical = self._canonical(unsigned)
        algorithm = signature.get("algorithm")
        if algorithm == "hmac-sha256" and self.key:
            expected = hmac.new(self.key, canonical, hashlib.sha256).hexdigest()
        elif algorithm == "sha256":
            expected = hashlib.sha256(canonical).hexdigest()
        else:
            return False
        return hmac.compare_digest(expected, str(signature.get("value", "")))

    @staticmethod
    def _canonical(data: dict[str, Any]) -> bytes:
        return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")

    @staticmethod
    def _file_hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()


class EvidenceVerifier:
    """Verify manifest signature, artifacts, Merkle transitions, and PCAP frame hashes."""

    def __init__(self, key: str | None = None) -> None:
        self.signer = EvidenceSigner(key)

    def verify(self, manifest_path: Path | str) -> VerificationReport:
        path = Path(manifest_path).resolve()
        errors: list[str] = []
        checks: dict[str, bool] = {}
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return VerificationReport(False, {"manifest_readable": False}, [str(exc)])
        checks["manifest_signature"] = self.signer.verify_signature(manifest)
        artifacts: dict[str, Path] = {}
        for kind, metadata in manifest.get("artifacts", {}).items():
            artifact = (path.parent / metadata["file"]).resolve()
            contained = artifact.parent == path.parent
            checksum_ok = contained and artifact.is_file() and (
                self.signer._file_hash(artifact) == metadata.get("sha256")
            )
            checks[f"{kind}_checksum"] = checksum_ok
            if checksum_ok:
                artifacts[kind] = artifact
        if "veridag" in artifacts:
            proof = json.loads(artifacts["veridag"].read_text(encoding="utf-8"))
            checks["veridag_merkle"] = self._verify_proof(proof)
        if "apcap" in artifacts:
            capture = json.loads(artifacts["apcap"].read_text(encoding="utf-8"))
            checks["apcap_frames"] = self._verify_frames(capture)
        for name, passed in checks.items():
            if not passed:
                errors.append(f"Failed check: {name}")
        return VerificationReport(all(checks.values()) and bool(checks), checks, errors)

    @staticmethod
    def _verify_proof(proof: dict[str, Any]) -> bool:
        hashes: list[str] = []
        for node_id, node in proof.get("node_proofs", {}).items():
            expected = VeriDAGEngine.compute_node_merkle_hash(
                node_id,
                str(node["input_hash"]),
                str(node["output_hash"]),
                list(node.get("parent_hashes", [])),
            )
            if not hmac.compare_digest(expected, str(node.get("state_merkle_hash", ""))):
                return False
            hashes.append(expected)
        root = hashlib.sha256(":".join(sorted(hashes)).encode("utf-8")).hexdigest()
        return bool(hashes) and hmac.compare_digest(root, str(proof.get("final_merkle_root", "")))

    @staticmethod
    def _verify_frames(capture: dict[str, Any]) -> bool:
        frames = capture.get("frames", [])
        if capture.get("captured_frames") != len(frames):
            return False
        for frame in frames:
            raw = json.dumps(frame.get("payload", {}), sort_keys=True, default=str)
            expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
            if not hmac.compare_digest(expected, str(frame.get("hash", ""))):
                return False
        return True
