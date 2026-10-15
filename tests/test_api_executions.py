"""Tests for execution API routes."""

from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from agent_factory.api.main import app
from agent_factory.runtime.engine import Execution
from agent_factory.security.auth import User, get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticated_user():
    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1", email="user@example.com", roles=["user"]
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.unit
def test_get_execution_not_found():
    """Test getting non-existent execution."""
    with patch('agent_factory.api.routes.executions.runtime') as mock_runtime:
        mock_runtime.get_execution.return_value = None
        response = client.get("/api/v1/executions/nonexistent")
        assert response.status_code == 404


@pytest.mark.unit
def test_get_execution():
    """Test getting an execution."""
    mock_execution = Execution(
        id="test-execution",
        type="agent",
        entity_id="test-agent",
        status="completed",
        created_at=datetime.now(),
        completed_at=datetime.now(),
        result="success",
        error=None,
        metadata={}
    )
    
    with patch('agent_factory.api.routes.executions.runtime') as mock_runtime:
        mock_runtime.get_execution.return_value = mock_execution
        response = client.get("/api/v1/executions/test-execution")
        assert response.status_code == 200
        assert response.json()["id"] == "test-execution"
        assert response.json()["status"] == "completed"


@pytest.mark.unit
def test_get_execution_logs():
    """Test getting execution logs."""
    mock_execution = Execution(
        id="test-execution",
        type="agent",
        entity_id="test-agent",
        status="error",
        created_at=datetime.now(),
        completed_at=datetime.now(),
        result=None,
        error="Test error",
        metadata={}
    )
    
    with patch('agent_factory.api.routes.executions.runtime') as mock_runtime:
        mock_runtime.get_execution.return_value = mock_execution
        response = client.get("/api/v1/executions/test-execution/logs")
        assert response.status_code == 200
        assert "logs" in response.json()
