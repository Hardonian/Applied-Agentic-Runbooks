"""Agent API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent_factory.agents.agent import Agent
from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.runtime.engine import RuntimeEngine

router = APIRouter()
registry = LocalRegistry()
runtime = RuntimeEngine()


class AgentCreate(BaseModel):
    id: str
    name: str
    instructions: str
    model: str = "gpt-4o"


class AgentRun(BaseModel):
    input_text: str
    session_id: str | None = None
    context: dict | None = None


@router.post("/", response_model=dict)
def create_agent(agent_data: AgentCreate):
    """Create a new agent."""
    agent = Agent(
        id=agent_data.id,
        name=agent_data.name,
        instructions=agent_data.instructions,
        model=agent_data.model,
    )

    registry.register_agent(agent)
    runtime.register_agent(agent)

    return {"id": agent.id, "status": "created"}


@router.get("/", response_model=list[dict])
def list_agents():
    """List all agents."""
    agent_ids = registry.list_agents()
    agents = []

    for agent_id in agent_ids:
        agent = registry.get_agent(agent_id)
        if agent:
            agents.append(agent.to_dict())

    return agents


@router.get("/{agent_id}", response_model=dict)
def get_agent(agent_id: str):
    """Get agent by ID."""
    agent = registry.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent.to_dict()


@router.post("/{agent_id}/run", response_model=dict)
def run_agent(agent_id: str, run_data: AgentRun):
    """Run an agent."""
    agent = registry.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = agent.run(
        run_data.input_text,
        session_id=run_data.session_id,
        context=run_data.context,
    )

    return {
        "output": result.output,
        "status": result.status.value,
        "execution_time": result.execution_time,
        "error": result.error,
    }


@router.delete("/{agent_id}")
def delete_agent(agent_id: str):
    """Delete an agent."""
    if not registry.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"status": "deleted"}
