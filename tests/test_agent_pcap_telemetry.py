"""
Tests for AgentPCAP packet capture and deterministic pathology debugger.
"""

import pytest

from agent_factory.telemetry.pcap import (
    AgentPCAPTracer,
    FrameType,
    PathologyType,
)


@pytest.mark.unit
def test_pcap_frame_capture_and_export():
    """Verify frames are timestamped, hashed, and exported to .apcap."""
    tracer = AgentPCAPTracer()

    tracer.record_frame(
        frame_type=FrameType.A2A,
        source="planner",
        destination="coder",
        payload={"task": "Implement feature"},
        tokens_used=120,
    )
    tracer.record_frame(
        frame_type=FrameType.TOOL,
        source="coder",
        destination="linter",
        payload={"tool_name": "ast_lint", "success": True},
        tokens_used=40,
    )

    data = tracer.export_apcap()
    assert data["captured_frames"] == 2
    assert data["total_tokens"] == 160
    assert len(data["frames"]) == 2


@pytest.mark.unit
def test_pcap_retry_storm_detection():
    """Verify deterministic detector catches tool retry storm pathology."""
    tracer = AgentPCAPTracer()

    failing_payload = {
        "tool_name": "db_query",
        "query": "SELECT * FROM missing",
        "success": False,
        "error": "Table not found",
    }

    for _ in range(3):
        tracer.record_frame(
            frame_type=FrameType.TOOL,
            source="analyst",
            destination="db",
            payload=failing_payload,
            tokens_used=200,
        )

    diagnostics = tracer.diagnose_pathologies()
    assert len(diagnostics) == 1
    assert diagnostics[0].pathology_type == PathologyType.RETRY_STORM
    assert diagnostics[0].severity == "CRITICAL"
    assert "3 consecutive times" in diagnostics[0].description
