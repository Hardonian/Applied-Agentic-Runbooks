"""Tests for tool API routes."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from agent_factory.api.main import app
from agent_factory.security.auth import User, get_current_user
from agent_factory.tools.base import Tool

client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticated_user():
    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1", email="user@example.com", roles=["user"]
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.unit
def test_list_tools_empty():
    """Test listing tools when none exist."""
    with patch("agent_factory.api.routes.tools.registry") as mock_registry:
        mock_registry.list_tools.return_value = []
        response = client.get("/api/v1/tools/")
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.unit
def test_list_tools():
    """Test listing tools."""
    with patch("agent_factory.api.routes.tools.registry") as mock_registry:
        mock_registry.list_tools.return_value = ["tool1", "tool2"]
        response = client.get("/api/v1/tools/")
        assert response.status_code == 200
        assert response.json() == ["tool1", "tool2"]


@pytest.mark.unit
def test_get_tool_not_found():
    """Test getting non-existent tool."""
    with patch("agent_factory.api.routes.tools.registry") as mock_registry:
        mock_registry.get_tool.return_value = None
        response = client.get("/api/v1/tools/nonexistent")
        assert response.status_code == 404


@pytest.mark.unit
def test_get_tool():
    """Test getting a tool."""
    mock_tool = Mock(spec=Tool)
    mock_tool.to_dict.return_value = {
        "id": "test-tool",
        "name": "Test Tool",
        "description": "A test tool",
    }

    with patch("agent_factory.api.routes.tools.registry") as mock_registry:
        mock_registry.get_tool.return_value = mock_tool
        response = client.get("/api/v1/tools/test-tool")
        assert response.status_code == 200
        assert response.json()["id"] == "test-tool"


@pytest.mark.unit
def test_get_tool_schema():
    """Test getting tool schema."""
    mock_tool = Mock(spec=Tool)
    mock_tool.get_schema.return_value = {
        "type": "function",
        "parameters": {"type": "object", "properties": {"x": {"type": "string"}}},
    }

    with patch("agent_factory.api.routes.tools.registry") as mock_registry:
        mock_registry.get_tool.return_value = mock_tool
        response = client.get("/api/v1/tools/test-tool/schema")
        assert response.status_code == 200
        assert "parameters" in response.json()


@pytest.mark.unit
def test_test_tool():
    """Test testing a tool."""
    mock_tool = Mock(spec=Tool)
    mock_tool.execute.return_value = "result"

    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1", email="test@example.com", roles=["user"]
    )
    try:
        with patch("agent_factory.api.routes.tools.registry") as mock_registry:
            mock_registry.get_tool.return_value = mock_tool
            response = client.post("/api/v1/tools/test-tool/test", json={"params": {"x": "test"}})
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert response.json()["result"] == "result"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.unit
def test_tool_test_requires_authentication():
    app.dependency_overrides.pop(get_current_user, None)
    response = client.post("/api/v1/tools/test-tool/test", json={"params": {}})
    assert response.status_code in {401, 403}
