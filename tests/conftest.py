"""Pytest configuration and shared fixtures."""

import os
os.environ["TESTING"] = "true"

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from agent_factory.agents.agent import Agent, AgentConfig
from agent_factory.tools.base import Tool
from agent_factory.workflows.model import Workflow, WorkflowStep
from agent_factory.core.memory import MemoryStore
from agent_factory.core.guardrails import Guardrails


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Mocked response"
    mock_response.choices[0].message.tool_calls = None
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 100
    
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    return Agent(
        id="test-agent",
        name="Test Agent",
        instructions="You are a test agent.",
    )


@pytest.fixture
def sample_tool():
    """Create a sample tool for testing."""
    def dummy_function(x: str) -> str:
        return f"Processed: {x}"
    
    return Tool(
        id="test-tool",
        name="Test Tool",
        description="A test tool",
        implementation=dummy_function,
    )


@pytest.fixture
def sample_workflow_step():
    """Create a sample workflow step."""
    return WorkflowStep(
        id="step1",
        agent_id="test-agent",
    )


@pytest.fixture
def sample_workflow(sample_workflow_step):
    """Create a sample workflow."""
    return Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[sample_workflow_step],
    )


@pytest.fixture
def mock_memory_store():
    """Mock memory store for testing."""
    mock_memory = Mock(spec=MemoryStore)
    mock_memory.get_context.return_value = {}
    mock_memory.save_interaction.return_value = None
    return mock_memory


@pytest.fixture
def mock_guardrails():
    """Mock guardrails for testing."""
    mock_guardrails = Mock(spec=Guardrails)
    mock_result = Mock()
    mock_result.allowed = True
    mock_result.reason = None
    mock_guardrails.validate_input.return_value = mock_result
    mock_guardrails.validate_output.return_value = mock_result
    return mock_guardrails


@pytest.fixture
def agents_registry(sample_agent):
    """Create a registry of agents for testing."""
    return {"test-agent": sample_agent}
