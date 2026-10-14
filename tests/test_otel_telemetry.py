"""Tests for OpenTelemetry exporter bridge."""

from __future__ import annotations

import time

from agent_factory.orchestration.veridag import VeriDAGExecutionProof
from agent_factory.telemetry.otel_exporter import OTelExporter
from agent_factory.telemetry.pcap import FrameType, PCAPFrame


def test_otel_exporter_frames_to_otlp():
    """Verify PCAP frames convert to valid OTLP JSON logs format."""
    exporter = OTelExporter(service_name="test-agent-factory")
    frame = PCAPFrame(
        frame_id="frame-001",
        timestamp=time.time(),
        frame_type=FrameType.TOOL,
        source="agent",
        destination="tool",
        payload={"action": "read_file"},
    )

    otlp_payload = exporter.frames_to_otlp([frame])
    assert "resourceLogs" in otlp_payload
    resource_logs = otlp_payload["resourceLogs"]
    assert len(resource_logs) == 1
    log_records = resource_logs[0]["scopeLogs"][0]["logRecords"]
    assert len(log_records) == 1
    assert log_records[0]["body"]["stringValue"] == "tool_call"


def test_otel_exporter_veridag_to_spans():
    """Verify VeriDAG cryptographic proof converts to OTLP trace spans."""
    exporter = OTelExporter()
    proof = VeriDAGExecutionProof(
        dag_id="dag-test-01",
        execution_id="exec-test-01",
        step_order=["step-1", "step-2"],
        step_hashes={"step-1": "hash1", "step-2": "hash2"},
        state_transitions=[
            {"step_id": "step-1", "pre_state_hash": "h0", "post_state_hash": "h1"},
            {"step_id": "step-2", "pre_state_hash": "h1", "post_state_hash": "h2"},
        ],
        merkle_tree_levels=[["leaf1", "leaf2"], ["root"]],
        final_merkle_root="0xabcdef1234567890",
        timestamp=time.time(),
        proof_signature="sig-test",
    )

    spans_payload = exporter.veridag_to_otlp_spans(proof)
    assert "resourceSpans" in spans_payload
    resource_spans = spans_payload["resourceSpans"]
    assert len(resource_spans) == 1
    spans = resource_spans[0]["scopeSpans"][0]["spans"]
    assert len(spans) == 3  # Root DAG span + 2 step spans


def test_otel_exporter_prometheus_metrics():
    """Verify metrics conversion produces valid Prometheus text exposition."""
    exporter = OTelExporter()
    metrics = {
        "pass_rate": 1.0,
        "pareto_frontier_score": 0.85,
        "p95_latency_ms": 12.4,
    }
    prom_text = exporter.metrics_to_prometheus(metrics, prefix="agent_factory_arena")
    assert "agent_factory_arena_pass_rate 1.0" in prom_text
    assert "agent_factory_arena_pareto_frontier_score 0.85" in prom_text
