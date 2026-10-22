"""Tests for Anthropic client integration."""

import os
from unittest.mock import Mock, patch

import pytest

from agent_factory.integrations.anthropic_client import AnthropicAgentClient


@pytest.mark.unit
def test_anthropic_client_init_no_key():
    """Test Anthropic client initialization without API key."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="API key required"):
            AnthropicAgentClient()


@pytest.mark.unit
def test_anthropic_client_init_with_key():
    """Test Anthropic client initialization with API key."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        client = AnthropicAgentClient()
        assert client.api_key == "test-key"


@pytest.mark.unit
def test_anthropic_client_run_agent():
    """Test running agent with Anthropic client."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        client = AnthropicAgentClient()

        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Test response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        with patch.object(client.client.messages, "create", return_value=mock_response):
            result = client.run_agent(instructions="You are a test agent", input_text="Hello")

            assert result["output"] == "Test response"
            assert result["tokens_used"] == 30
