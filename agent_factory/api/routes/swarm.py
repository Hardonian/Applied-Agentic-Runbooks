"""
Multi-Agent Swarm Orchestration & Enterprise Compliance API Routes.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from agent_factory.agents.agent import Agent, AgentConfig
from agent_factory.compliance.certification import AgentCertificationGenerator
from agent_factory.core.guardrails import Guardrails, SQLInjectionGuardrail
from agent_factory.orchestration.swarm import SwarmOrchestrator, SwarmPattern, SwarmResult

router = APIRouter()
compliance_router = APIRouter()


class SwarmAgentSpec(BaseModel):
    id: str
    name: str | None = None
    instructions: str | None = None
    model: str = "gpt-4o"


class SwarmExecuteRequest(BaseModel):
    task: str = Field(..., description="Objective for multi-agent swarm")
    pattern: str = Field(
        "hierarchical",
        description="Swarm topology: hierarchical, peer_debate, voting_consensus, dynamic_router",
    )
    agents: list[SwarmAgentSpec] | None = None
    supervisor: SwarmAgentSpec | None = None
    max_rounds: int = Field(4, ge=1, le=10)
    context: dict[str, Any] | None = None


class AgentCertifyRequest(BaseModel):
    agent_id: str = Field(..., description="Agent unique identifier")
    name: str | None = None
    instructions: str = Field(
        "Enterprise Autonomous Agent", description="System prompt instructions"
    )
    model: str = Field("gpt-4o", description="Target foundation model")
    enable_guardrails: bool = Field(True, description="Attach enterprise safety guardrails")


@router.post("/execute", response_model=dict[str, Any])
def execute_swarm(request: SwarmExecuteRequest):
    """
    Execute a collaborative multi-agent swarm.
    """
    try:
        swarm_pattern = SwarmPattern(request.pattern)
    except ValueError:
        valid_patterns = [p.value for p in SwarmPattern]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid swarm pattern '{request.pattern}'. Allowed: {valid_patterns}",
        )

    # Initialize worker agents
    worker_specs = request.agents or [
        SwarmAgentSpec(
            id="researcher", name="Lead Researcher", instructions="Conduct in-depth fact finding."
        ),
        SwarmAgentSpec(
            id="analyst",
            name="Strategic Analyst",
            instructions="Synthesize and evaluate strategic risk.",
        ),
        SwarmAgentSpec(
            id="synthesizer",
            name="Chief Synthesizer",
            instructions="Integrate consensus decisions into clear action items.",
        ),
    ]
    swarm_agents = [
        Agent(
            id=spec.id,
            name=spec.name or spec.id.title(),
            instructions=spec.instructions or f"Specialist in {spec.id}",
            model=spec.model,
        )
        for spec in worker_specs
    ]

    # Initialize supervisor if hierarchical
    supervisor_agent = None
    if request.supervisor:
        supervisor_agent = Agent(
            id=request.supervisor.id,
            name=request.supervisor.name or "Supervisor",
            instructions=request.supervisor.instructions or "Lead and coordinate the team.",
            model=request.supervisor.model,
        )
    elif swarm_pattern == SwarmPattern.HIERARCHICAL:
        supervisor_agent = Agent(
            id="supervisor",
            name="Swarm Supervisor",
            instructions="Lead and coordinate the team.",
            model="gpt-4o",
        )

    orchestrator = SwarmOrchestrator(
        agents=swarm_agents,
        supervisor=supervisor_agent,
        pattern=swarm_pattern,
        max_rounds=request.max_rounds,
    )

    result: SwarmResult = orchestrator.execute(task=request.task, context=request.context)

    return {
        "status": result.status.value,
        "pattern": result.pattern.value,
        "task": request.task,
        "final_output": result.final_output,
        "execution_time": result.execution_time,
        "consensus_score": result.consensus_score,
        "winning_candidate": result.winning_candidate,
        "total_messages": len(result.messages),
        "messages": [
            {
                "agent_id": m.agent_id,
                "agent_name": m.agent_name,
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
            }
            for m in result.messages
        ],
    }


@compliance_router.post("/certify", response_model=dict[str, Any])
def certify_agent(request: AgentCertifyRequest):
    """
    Generate an enterprise compliance certificate (SOC 2, HIPAA, EU AI Act, OWASP Top 10) for an agent.
    """
    guardrails = None
    if request.enable_guardrails:
        guardrails = Guardrails()
        guardrails.add_input_guardrail(SQLInjectionGuardrail())

    agent = Agent(
        id=request.agent_id,
        name=request.name or request.agent_id.title(),
        instructions=request.instructions,
        model=request.model,
        guardrails=guardrails,
        config=AgentConfig(max_tokens=4096, timeout=30),
    )

    cert = AgentCertificationGenerator.generate_certificate(agent)

    return {
        "certificate": cert.to_dict(),
        "markdown_report": cert.to_markdown(),
    }
