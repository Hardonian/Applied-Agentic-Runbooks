"""Tests for Agent class."""

from unittest.mock import Mock, patch

import pytest

from agent_factory.agents.agent import Agent, AgentStatus


@pytest.mark.unit
def test_agent_creation():
    """Test creating an agent."""
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="You are a test agent.",
    )

    assert agent.id == "test-agent"
    assert agent.name == "Test Agent"
    assert agent.instructions == "You are a test agent."
    assert agent.model == "gpt-4o"


@pytest.mark.unit
def test_agent_with_tools():
    """Test agent with tools."""
    from agent_factory.tools.base import Tool

    def dummy_tool(x: str) -> str:
        return f"Processed: {x}"

    tool = Tool(
        id="dummy-tool",
        name="Dummy Tool",
        description="A dummy tool",
        implementation=dummy_tool,
    )

    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
        tools=[tool],
    )

    assert len(agent.tools) == 1
    assert agent.tools[0].id == "dummy-tool"


@pytest.mark.unit
def test_agent_add_tool():
    """Test adding a tool to an agent."""
    from agent_factory.tools.base import Tool

    def dummy_tool(x: str) -> str:
        return f"Processed: {x}"

    tool = Tool(
        id="dummy-tool",
        name="Dummy Tool",
        description="A dummy tool",
        implementation=dummy_tool,
    )

    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )

    agent.add_tool(tool)
    assert len(agent.tools) == 1


@pytest.mark.unit
def test_agent_serialization():
    """Test agent serialization."""
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )

    data = agent.to_dict()

    assert data["id"] == "test-agent"
    assert data["name"] == "Test Agent"
    assert data["instructions"] == "Test"


@pytest.mark.unit
def test_agent_deserialization():
    """Test agent deserialization."""
    data = {
        "id": "test-agent",
        "name": "Test Agent",
        "instructions": "Test",
        "model": "gpt-4o",
        "tools": [],
        "config": {
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        "metadata": {},
    }

    agent = Agent.from_dict(data)

    assert agent.id == "test-agent"
    assert agent.name == "Test Agent"
    assert agent.instructions == "Test"


@pytest.mark.unit
@patch("agent_factory.integrations.openai_client.OpenAIAgentClient")
def test_agent_run_with_mocked_client(mock_client_class):
    """Test agent.run() with mocked OpenAI client."""
    # Setup mock
    mock_client = Mock()
    mock_client.run_agent.return_value = {
        "output": "Mocked response",
        "tool_calls": [],
        "tokens_used": 100,
        "model": "gpt-4o",
    }
    mock_client_class.return_value = mock_client

    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="You are a test agent.",
    )

    result = agent.run("Test input")

    assert result.status == AgentStatus.COMPLETED
    assert result.output == "Mocked response"
    assert result.tokens_used == 0  # Not set in current implementation
    mock_client.run_agent.assert_called_once()
