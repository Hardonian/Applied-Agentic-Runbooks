"""Tests for workflow API routes."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from agent_factory.api.main import app
from agent_factory.security.auth import User, get_current_user
from agent_factory.workflows.model import Workflow

client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticated_user():
    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1", email="user@example.com", roles=["user"]
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.unit
def test_list_workflows():
    """Test listing workflows."""
    with patch('agent_factory.api.routes.workflows.registry') as mock_registry:
        mock_registry.list_workflows.return_value = ["workflow1", "workflow2"]
        response = client.get("/api/v1/workflows/")
        assert response.status_code == 200
        assert response.json() == ["workflow1", "workflow2"]


@pytest.mark.unit
def test_get_workflow_not_found():
    """Test getting non-existent workflow."""
    with patch('agent_factory.api.routes.workflows.registry') as mock_registry:
        mock_registry.get_workflow.return_value = None
        response = client.get("/api/v1/workflows/nonexistent")
        assert response.status_code == 404


@pytest.mark.unit
def test_get_workflow():
    """Test getting a workflow."""
    mock_workflow = Mock(spec=Workflow)
    mock_workflow.to_dict.return_value = {
        "id": "test-workflow",
        "name": "Test Workflow",
        "steps": []
    }
    
    with patch('agent_factory.api.routes.workflows.registry') as mock_registry:
        mock_registry.get_workflow.return_value = mock_workflow
        response = client.get("/api/v1/workflows/test-workflow")
        assert response.status_code == 200
        assert response.json()["id"] == "test-workflow"


@pytest.mark.unit
def test_get_workflow_status():
    """Test getting workflow status."""
    mock_workflow = Mock(spec=Workflow)
    
    with patch('agent_factory.api.routes.workflows.registry') as mock_registry, \
         patch('agent_factory.api.routes.workflows.runtime') as mock_runtime:
        mock_registry.get_workflow.return_value = mock_workflow
        mock_runtime.list_executions.return_value = []
        
        response = client.get("/api/v1/workflows/test-workflow/status")
        assert response.status_code == 200
        assert "recent_executions" in response.json()
