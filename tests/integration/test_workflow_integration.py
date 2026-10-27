"""Integration tests for workflows with agents."""

from unittest.mock import MagicMock, patch

import pytest

from agent_factory.agents.agent import Agent
from agent_factory.workflows.model import Workflow, WorkflowStep


@pytest.mark.integration
@patch("agent_factory.integrations.openai_client.OpenAIAgentClient")
def test_workflow_execution_with_agents(mock_client_class):
    """Test workflow execution with real agent instances."""
    # Setup mock OpenAI client
    mock_client = MagicMock()
    mock_client.run_agent.return_value = {
        "output": "Mocked agent response",
        "tool_calls": [],
        "tokens_used": 100,
    }
    mock_client_class.return_value = mock_client

    # Create agents
    agent1 = Agent(
        id="agent-1",
        name="Agent 1",
        instructions="You are agent 1",
    )

    agent2 = Agent(
        id="agent-2",
        name="Agent 2",
        instructions="You are agent 2",
    )

    # Create workflow
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[
            WorkflowStep(id="step1", agent_id="agent-1"),
            WorkflowStep(id="step2", agent_id="agent-2"),
        ],
        agents_registry={
            "agent-1": agent1,
            "agent-2": agent2,
        },
    )

    # Execute workflow
    result = workflow.execute({"input": "test"})

    assert result.success is True
    assert len(result.steps_executed) == 2
    assert "step1" in result.steps_executed
    assert "step2" in result.steps_executed


@pytest.mark.integration
def test_workflow_with_missing_agent():
    """Test workflow execution when agent is missing."""
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[
            WorkflowStep(id="step1", agent_id="missing-agent"),
        ],
        agents_registry={},
    )

    result = workflow.execute({"input": "test"})

    assert result.success is False
    assert "not found" in result.error.lower()
