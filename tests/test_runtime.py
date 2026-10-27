"""Tests for Runtime Engine."""

from unittest.mock import Mock, patch

import pytest

from agent_factory.agents.agent import Agent
from agent_factory.runtime.engine import RuntimeEngine
from agent_factory.workflows.model import Workflow


@pytest.mark.unit
def test_runtime_engine_initialization():
    """Test runtime engine initialization."""
    engine = RuntimeEngine()
    assert engine.agents_registry == {}
    assert engine.workflows_registry == {}
    assert engine.executions == {}


@pytest.mark.unit
def test_register_agent():
    """Test registering an agent."""
    engine = RuntimeEngine()
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )

    engine.register_agent(agent)
    assert "test-agent" in engine.agents_registry
    assert engine.agents_registry["test-agent"] == agent


@pytest.mark.unit
def test_register_workflow():
    """Test registering a workflow."""
    engine = RuntimeEngine()
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[],
    )

    engine.register_workflow(workflow)
    assert "test-workflow" in engine.workflows_registry
    assert engine.workflows_registry["test-workflow"] == workflow


@pytest.mark.unit
def test_run_workflow_preserves_hydrated_agents_and_start_step():
    """A persisted workflow can run after its agent bindings are rehydrated."""
    engine = RuntimeEngine()
    workflow = Mock(spec=Workflow)
    workflow.id = "test-workflow"
    workflow.steps = [Mock(id="first"), Mock(id="second")]
    workflow.agents_registry = {"persisted-agent": Mock()}
    workflow.execute.return_value = Mock(
        execution_time=0.1,
        steps_completed=1,
        steps_total=1,
        tokens_used=0,
        cost_estimate=0.0,
    )

    engine.register_workflow(workflow)
    execution_id = engine.run_workflow("test-workflow", {"input": "test"}, start_step="second")

    assert "persisted-agent" in engine.agents_registry
    workflow.execute.assert_called_once_with({"input": "test"}, start_step="second")
    assert engine.get_execution(execution_id).metadata["start_step"] == "second"


@pytest.mark.unit
def test_run_workflow_rejects_unknown_start_step():
    engine = RuntimeEngine()
    workflow = Mock(spec=Workflow)
    workflow.id = "test-workflow"
    workflow.steps = [Mock(id="first")]
    workflow.agents_registry = {}
    engine.register_workflow(workflow)

    with pytest.raises(ValueError, match="Workflow step not found"):
        engine.run_workflow("test-workflow", {}, start_step="missing")


@pytest.mark.unit
@patch("agent_factory.integrations.openai_client.OpenAIAgentClient")
def test_run_agent(mock_client_class):
    """Test running an agent via runtime engine."""
    mock_client = Mock()
    mock_client.run_agent.return_value = {
        "output": "Test output",
        "tool_calls": [],
        "tokens_used": 50,
    }
    mock_client_class.return_value = mock_client

    engine = RuntimeEngine()
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )

    engine.register_agent(agent)
    execution_id = engine.run_agent("test-agent", "Test input")

    assert execution_id is not None
    execution = engine.get_execution(execution_id)
    assert execution is not None
    assert execution.status == "completed"


@pytest.mark.unit
def test_run_agent_not_found():
    """Test running non-existent agent."""
    engine = RuntimeEngine()

    with pytest.raises(ValueError, match="Agent not found"):
        engine.run_agent("non-existent", "Test")


@pytest.mark.unit
def test_get_execution():
    """Test getting execution by ID."""
    engine = RuntimeEngine()
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )

    engine.register_agent(agent)

    with patch("agent_factory.integrations.openai_client.OpenAIAgentClient"):
        execution_id = engine.run_agent("test-agent", "Test")
        execution = engine.get_execution(execution_id)
        assert execution is not None
        assert execution.id == execution_id


@pytest.mark.unit
def test_list_executions():
    """Test listing executions."""
    engine = RuntimeEngine()
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )

    engine.register_agent(agent)

    with patch("agent_factory.integrations.openai_client.OpenAIAgentClient"):
        execution_id = engine.run_agent("test-agent", "Test")
        executions = engine.list_executions()
        assert len(executions) == 1
        assert executions[0].id == execution_id
