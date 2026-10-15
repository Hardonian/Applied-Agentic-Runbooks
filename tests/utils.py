"""Test utilities and helpers."""

from agent_factory.agents.agent import Agent
from agent_factory.tools.base import Tool
from agent_factory.workflows.model import Workflow, WorkflowStep


def create_test_agent(
    agent_id: str = "test-agent",
    name: str = "Test Agent",
    instructions: str = "You are a test agent.",
    model: str = "gpt-4o",
) -> Agent:
    """
    Create a test agent.
    
    Args:
        agent_id: Agent ID
        name: Agent name
        instructions: Agent instructions
        model: LLM model
        
    Returns:
        Agent instance
    """
    return Agent(
        id=agent_id,
        name=name,
        instructions=instructions,
        model=model,
    )


def create_test_tool(
    tool_id: str = "test-tool",
    name: str = "Test Tool",
    description: str = "A test tool",
) -> Tool:
    """
    Create a test tool.
    
    Args:
        tool_id: Tool ID
        name: Tool name
        description: Tool description
        
    Returns:
        Tool instance
    """
    def dummy_function(x: str) -> str:
        return f"Processed: {x}"
    
    return Tool(
        id=tool_id,
        name=name,
        description=description,
        implementation=dummy_function,
    )


def create_test_workflow(
    workflow_id: str = "test-workflow",
    name: str = "Test Workflow",
    agent_ids: list[str] | None = None,
    agents_registry: dict[str, Agent] | None = None,
) -> Workflow:
    """
    Create a test workflow.
    
    Args:
        workflow_id: Workflow ID
        name: Workflow name
        agent_ids: List of agent IDs for steps
        agents_registry: Registry of agents
        
    Returns:
        Workflow instance
    """
    if agent_ids is None:
        agent_ids = ["test-agent"]
    
    steps = [
        WorkflowStep(id=f"step-{i}", agent_id=agent_id)
        for i, agent_id in enumerate(agent_ids, start=1)
    ]
    
    return Workflow(
        id=workflow_id,
        name=name,
        steps=steps,
        agents_registry=agents_registry or {},
    )
