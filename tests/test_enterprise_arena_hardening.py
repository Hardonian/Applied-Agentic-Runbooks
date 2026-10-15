"""Production-hardening tests for durable Arena, replay, approvals, and evidence."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent_factory.api.main import app
from agent_factory.api.ws.event_bus import EventBus
from agent_factory.evaluation.arena import ArenaRunner, GauntletSuite
from agent_factory.evaluation.arena.evidence import EvidenceVerifier
from agent_factory.security.approval import ApprovalAuthority
from agent_factory.security.mcpwall import MCPWall


def test_durable_async_job_history_and_comparison() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/arena/jobs",
            json={"suites": ["settler_accounting"], "concurrency": 4, "trials": 2},
        )
        assert response.status_code == 202
        job = response.json()
        assert response.headers["location"].endswith(job["run_id"])

        record = None
        for _ in range(100):
            record = client.get(job["status_url"]).json()
            if record["status"] in {"passed", "failed", "cancelled"}:
                break
            time.sleep(0.01)
        assert record is not None and record["status"] == "passed"
        assert record["summary"]["suites"][0]["details"]["trials"] == 2

        history = client.get("/api/v1/arena/runs").json()
        assert any(item["run_id"] == job["run_id"] for item in history["entries"])
        comparison = client.get(f"/api/v1/arena/compare?ids={job['run_id']}").json()
        assert comparison["entries"][0]["run_id"] == job["run_id"]


@pytest.mark.asyncio
async def test_event_bus_replays_after_cursor_and_counts_drops() -> None:
    bus = EventBus(queue_size=1, history_size=5)
    first = await bus.publish("run", {"type": "one"})
    await bus.publish("run", {"type": "two"})
    queue = bus.subscribe("run", after_sequence=first["sequence"])
    assert (await asyncio.wait_for(queue.get(), 1))["type"] == "two"
    await bus.publish("run", {"type": "three"})
    await bus.publish("run", {"type": "four"})
    assert bus.dropped_events >= 1


def test_authoritative_approval_receipt_and_single_use() -> None:
    tenant = f"tenant-{uuid.uuid4().hex}"
    authority = ApprovalAuthority(signing_key="unit-test-key")
    wall = MCPWall(ticket_store=authority, destructive_tools={"write_file"})
    arguments = {"path": str(Path.cwd() / "approved.txt")}
    verdict = wall.validate_tool_call(
        "write_file", arguments, tenant_id=tenant, requested_by="requester"
    )
    assert verdict.ticket is not None
    receipt = authority.resolve(
        verdict.ticket.ticket_id,
        "approved",
        "security-operator",
        tenant_id=tenant,
        roles={"security"},
        reason="Validated change ticket",
    )
    assert authority.verify_receipt(receipt)
    assert wall.validate_tool_call(
        "write_file", arguments, verdict.ticket.ticket_id, tenant_id=tenant
    ).allowed
    assert not wall.validate_tool_call(
        "write_file", arguments, verdict.ticket.ticket_id, tenant_id=tenant
    ).allowed


@pytest.mark.asyncio
async def test_signed_evidence_bundle_detects_tampering(tmp_path: Path) -> None:
    summary = await ArenaRunner(tmp_path).run([GauntletSuite.REASONING_FRONTIER])
    manifest = Path(summary.artifact_paths["manifest"])
    assert EvidenceVerifier().verify(manifest).valid
    capture = Path(summary.artifact_paths["apcap"])
    payload = json.loads(capture.read_text(encoding="utf-8"))
    payload["frames"][0]["payload"]["tampered"] = True
    capture.write_text(json.dumps(payload), encoding="utf-8")
    report = EvidenceVerifier().verify(manifest)
    assert not report.valid
    assert not report.checks["apcap_checksum"]


def test_studio_has_enterprise_controls_and_no_inline_styles() -> None:
    html = Path("agent_factory/ui/studio/index.html").read_text(encoding="utf-8")
    assert "style=" not in html
    for control in ["cancel-arena", "run-history", "compare-runs", "frame-filter"]:
        assert f'id="{control}"' in html
