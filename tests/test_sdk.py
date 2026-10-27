"""Tests for SDK client."""

import os
from unittest.mock import Mock, patch

import pytest

from agent_factory.sdk.client import Client


@pytest.mark.unit
def test_sdk_client_initialization():
    """Test SDK client initialization."""
    client = Client(api_key="test-key", base_url="http://test.com")

    assert client.api_key == "test-key"
    assert client.base_url == "http://test.com"
    assert client.timeout == 30.0


@pytest.mark.unit
def test_sdk_client_env_vars():
    """Test SDK client uses environment variables."""
    with patch.dict(
        os.environ,
        {
            "AGENT_FACTORY_API_KEY": "env-key",
            "AGENT_FACTORY_API_URL": "http://env.com",
        },
    ):
        client = Client()

        assert client.api_key == "env-key"
        assert client.base_url == "http://env.com"


@pytest.mark.unit
@patch("httpx.Client")
def test_sdk_client_http_headers(mock_client_class):
    """Test SDK client sets HTTP headers correctly."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client

    Client(api_key="test-key")

    assert mock_client_class.called
    call_kwargs = mock_client_class.call_args[1]
    assert "Authorization" in call_kwargs["headers"]
    assert call_kwargs["headers"]["Authorization"] == "Bearer test-key"


@pytest.mark.unit
@patch("httpx.Client")
def test_sdk_create_agent(mock_client_class):
    """Test creating an agent via SDK."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.json.return_value = {"id": "test-agent", "name": "Test"}
    mock_response.raise_for_status = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value = mock_client

    client = Client(api_key="test-key")
    result = client.create_agent("test-agent", "Test Agent", "Instructions")

    assert result["id"] == "test-agent"
    assert mock_client.request.called
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "POST"
    assert call_args[0][1] == "/api/v1/agents/"


@pytest.mark.unit
@patch("httpx.Client")
def test_sdk_run_agent(mock_client_class):
    """Test running an agent via SDK."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.json.return_value = {"output": "Hello"}
    mock_response.raise_for_status = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value = mock_client

    client = Client(api_key="test-key")
    result = client.run_agent("test-agent", "Hello!")

    assert result["output"] == "Hello"
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "POST"
    assert "/run" in call_args[0][1]


@pytest.mark.unit
@patch("httpx.Client")
def test_sdk_list_blueprints(mock_client_class):
    """Test listing blueprints via SDK."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.json.return_value = [{"id": "bp1"}, {"id": "bp2"}]
    mock_response.raise_for_status = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value = mock_client

    client = Client(api_key="test-key")
    blueprints = client.list_blueprints()

    assert len(blueprints) == 2
    assert blueprints[0]["id"] == "bp1"


@pytest.mark.unit
@patch("httpx.Client")
def test_sdk_context_manager(mock_client_class):
    """Test SDK client as context manager."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client

    with Client(api_key="test-key") as client:
        assert client is not None

    assert mock_client.close.called
