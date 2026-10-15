"""Tests for Workflow class."""

import pytest

from agent_factory.agents.agent import Agent
from agent_factory.workflows.model import Trigger, TriggerType, Workflow, WorkflowStep


@pytest.mark.unit
def test_workflow_creation():
    """Test creating a workflow."""
    step = WorkflowStep(
        id="step1",
        agent_id="agent1",
    )
    
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[step],
    )
    
    assert workflow.id == "test-workflow"
    assert workflow.name == "Test Workflow"
    assert len(workflow.steps) == 1


@pytest.mark.unit
def test_workflow_add_step():
    """Test adding a step to workflow."""
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[],
    )
    
    step = WorkflowStep(
        id="step1",
        agent_id="agent1",
    )
    
    workflow.add_step(step)
    assert len(workflow.steps) == 1


@pytest.mark.unit
def test_workflow_add_trigger():
    """Test adding a trigger to workflow."""
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[],
    )
    
    trigger = Trigger(
        type=TriggerType.WEBHOOK,
        config={"path": "/webhook"},
    )
    
    workflow.add_trigger(trigger)
    assert len(workflow.triggers) == 1


@pytest.mark.unit
def test_workflow_execution():
    """Test workflow execution."""
    # Create mock agent
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )
    
    step = WorkflowStep(
        id="step1",
        agent_id="test-agent",
    )
    
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[step],
        agents_registry={"test-agent": agent},
    )
    
    result = workflow.execute({"input": "test"})
    
    assert result.success is True
    assert "step1" in result.steps_executed
