"""
Tests for Advanced REST Endpoints (MCTS, Cascade, JIT, and MCPWall).
"""

import pytest
from fastapi.testclient import TestClient
from agent_factory.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.unit
def test_api_mcts_search(client):
    """Verify MCTS search REST endpoint."""
    payload = {
        "problem": "Resolve Byzantine consensus under network partitions",
        "max_depth": 2,
        "branching_factor": 3,
        "num_simulations": 4,
    }
    res = client.post("/api/v1/reasoning/mcts/search", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "confidence_score" in data
    assert "best_trajectory" in data
    assert len(data["best_trajectory"]) > 0


@pytest.mark.unit
def test_api_cascade_execute(client):
    """Verify speculative cascade REST endpoint."""
    payload = {
        "prompt": "Evaluate simple string formatting.",
        "force_tier": "fast",
    }
    res = client.post("/api/v1/optimization/cascade/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["tier_used"] == "fast"
    assert data["cost_savings_percentage"] > 50.0


@pytest.mark.unit
def test_api_jit_synthesize(client):
    """Verify JIT tool synthesis REST endpoint."""
    code = (
        "def multiply_by_three(val: int) -> int:\n"
        "    return val * 3\n"
    )
    payload = {
        "name": "multiply_by_three",
        "description": "Multiplies input by 3",
        "code": code,
        "sample_inputs": [{"val": 4}],
        "expected_outputs": [12],
    }
    res = client.post("/api/v1/tools/jit/synthesize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "compiled_and_verified"
    assert data["tool_name"] == "multiply_by_three"
    assert "integrity_hash" in data


@pytest.mark.unit
def test_api_mcpwall_validate(client):
    """Verify MCPWall zero-trust validation REST endpoint."""
    payload = {
        "tool_name": "delete_database",
        "arguments": {"db": "production"},
    }
    res = client.post("/api/v1/security/mcpwall/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["allowed"] is False
    assert "explicitly denied" in data["reason"]
