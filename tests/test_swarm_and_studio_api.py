"""
Tests for Swarm Orchestration, Studio UI mounting, and Compliance API routes.
"""

import pytest
from fastapi.testclient import TestClient

from agent_factory.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.unit
def test_root_and_studio_mount(client):
    """Verify root endpoint exposes studio and /studio serves HTML dashboard."""
    # Root check
    root_res = client.get("/")
    assert root_res.status_code == 200
    data = root_res.json()
    assert data["name"] == "Agent Factory Platform API"
    assert data["studio"] == "/studio"

    # Studio UI check
    studio_res = client.get("/studio/")
    assert studio_res.status_code == 200
    assert "Agent Factory Studio" in studio_res.text


@pytest.mark.unit
def test_swarm_execution_endpoint(client):
    """Verify swarm execution endpoint runs multi-agent collaborative workflows."""
    payload = {
        "task": "Analyze distributed consensus protocols for low-latency financial settlement.",
        "pattern": "hierarchical",
        "max_rounds": 2,
    }
    res = client.post("/api/v1/orchestration/swarm/execute", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "completed"
    assert body["pattern"] == "hierarchical"
    assert body["total_messages"] > 0
    assert "final_output" in body


@pytest.mark.unit
def test_compliance_certify_endpoint(client):
    """Verify compliance certification endpoint evaluates agent controls and outputs certificate."""
    payload = {
        "agent_id": "api-certified-agent",
        "name": "Production Settlement Agent",
        "instructions": "Safely execute financial validations under strict audit controls.",
        "model": "gpt-4o",
        "enable_guardrails": True,
    }
    res = client.post("/api/v1/compliance/certify", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "certificate" in body
    assert "markdown_report" in body
    cert = body["certificate"]
    assert cert["agent_id"] == "api-certified-agent"
    assert cert["overall_score"] >= 80
    assert "digital_seal" in cert
    assert "# 🛡️ Agent Factory Production Certification Record" in body["markdown_report"]
