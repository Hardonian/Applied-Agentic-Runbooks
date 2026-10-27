"""Tests for the OpenAI client adapter without a network dependency."""

from types import SimpleNamespace

import pytest

from agent_factory.integrations.openai_client import OpenAIAgentClient
from agent_factory.tools.base import Tool


def _client_with_completions(create):
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_openai_tool_call_arguments_are_decoded_from_json():
    client = OpenAIAgentClient(api_key="test-key", client=_client_with_completions(None))
    tool = Tool("echo", "Echo", "Echo text", implementation=lambda text: text)

    assert client.execute_tool_call(tool, '{"text": "hello"}') == "hello"
    with pytest.raises(ValueError, match="valid JSON"):
        client.execute_tool_call(tool, "not-json")


def test_openai_stream_agent_yields_text_deltas():
    chunks = [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="hello "))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="world"))]),
    ]
    client = OpenAIAgentClient(
        api_key="test-key", client=_client_with_completions(lambda **_kwargs: chunks)
    )

    assert "".join(client.stream_agent("Be helpful", "Hi")) == "hello world"
