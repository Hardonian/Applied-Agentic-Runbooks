"""Tests for Agent API routes."""

import pytest
from fastapi.testclient import TestClient

from agent_factory.api.main import app


@pytest.mark.unit
def test_create_agent():
    """Test creating an agent via API."""
    client = TestClient(app)

    response = client.post(
        "/api/v1/agents/",
        json={
            "id": "test-agent-api",
            "name": "Test Agent API",
            "instructions": "You are a test agent.",
            "model": "gpt-4o",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-agent-api"
    assert data["status"] == "created"


@pytest.mark.unit
def test_list_agents():
    """Test listing agents via API."""
    client = TestClient(app)

    # Create an agent first
    client.post(
        "/api/v1/agents/",
        json={
            "id": "test-agent-list",
            "name": "Test Agent List",
            "instructions": "Test",
        },
    )

    # List agents
    response = client.get("/api/v1/agents/")
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)


@pytest.mark.unit
def test_get_agent():
    """Test getting an agent via API."""
    client = TestClient(app)

    # Create an agent first
    client.post(
        "/api/v1/agents/",
        json={
            "id": "test-agent-get",
            "name": "Test Agent Get",
            "instructions": "Test",
        },
    )

    # Get agent
    response = client.get("/api/v1/agents/test-agent-get")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-agent-get"


@pytest.mark.unit
def test_get_agent_not_found():
    """Test getting a non-existent agent."""
    client = TestClient(app)

    response = client.get("/api/v1/agents/non-existent")
    assert response.status_code == 404


@pytest.mark.unit
def test_delete_agent():
    """Test deleting an agent via API."""
    client = TestClient(app)

    # Create an agent first
    client.post(
        "/api/v1/agents/",
        json={
            "id": "test-agent-delete",
            "name": "Test Agent Delete",
            "instructions": "Test",
        },
    )

    # Delete agent
    response = client.delete("/api/v1/agents/test-agent-delete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"


@pytest.mark.unit
def test_run_agent():
    """Test running an agent via API."""
    client = TestClient(app)

    # Create an agent first
    client.post(
        "/api/v1/agents/",
        json={
            "id": "test-agent-run",
            "name": "Test Agent Run",
            "instructions": "Test",
        },
    )

    # Run agent (will use mocked OpenAI client)
    response = client.post(
        "/api/v1/agents/test-agent-run/run",
        json={
            "input_text": "Hello",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "output" in data
    assert "status" in data
