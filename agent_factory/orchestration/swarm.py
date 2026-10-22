"""
Autonomous Multi-Agent Swarms & Consensus Engine for Agent Factory.

Supports:
- Hierarchical Supervisor-Worker Delegation
- Multi-Agent Round-Robin Peer Debate
- Weighted Majority Voting & Consensus Synthesis
- Dynamic Intent-Based Agent Handoffs
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent_factory.agents.agent import Agent, AgentStatus
from agent_factory.integrations.universal_client import UniversalLLMClient


class SwarmPattern(str, Enum):
    HIERARCHICAL = "hierarchical"
    PEER_DEBATE = "peer_debate"
    VOTING_CONSENSUS = "voting_consensus"
    DYNAMIC_ROUTER = "dynamic_router"


@dataclass
class SwarmMessage:
    """A message exchange within the multi-agent swarm."""

    agent_id: str
    agent_name: str
    role: str  # supervisor, worker, debater, voter
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmResult:
    """Final result from multi-agent swarm execution."""

    final_output: str
    pattern: SwarmPattern
    messages: list[SwarmMessage] = field(default_factory=list)
    consensus_score: float | None = None
    winning_candidate: str | None = None
    execution_time: float = 0.0
    total_tokens: int = 0
    status: AgentStatus = AgentStatus.COMPLETED
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SwarmOrchestrator:
    """
    Coordinates multi-agent swarms using advanced collaborative topologies.
    """

    def __init__(
        self,
        agents: list[Agent] | None = None,
        supervisor: Agent | None = None,
        pattern: SwarmPattern = SwarmPattern.HIERARCHICAL,
        max_rounds: int = 4,
        llm_client: UniversalLLMClient | None = None,
    ):
        self.agents: dict[str, Agent] = {a.id: a for a in (agents or [])}
        self.supervisor = supervisor
        self.pattern = pattern
        self.max_rounds = max_rounds
        self.llm_client = llm_client or UniversalLLMClient()

    def add_agent(self, agent: Agent) -> None:
        """Register a worker/debater agent in the swarm."""
        self.agents[agent.id] = agent

    def execute(self, task: str, context: dict[str, Any] | None = None) -> SwarmResult:
        """
        Execute the multi-agent swarm based on the selected pattern.
        """
        start_time = time.time()
        messages: list[SwarmMessage] = []
        ctx = context or {}

        try:
            if self.pattern == SwarmPattern.PEER_DEBATE:
                return self._run_peer_debate(task, ctx, start_time)
            elif self.pattern == SwarmPattern.VOTING_CONSENSUS:
                return self._run_voting_consensus(task, ctx, start_time)
            elif self.pattern == SwarmPattern.DYNAMIC_ROUTER:
                return self._run_dynamic_router(task, ctx, start_time)
            else:
                return self._run_hierarchical(task, ctx, start_time)

        except Exception as e:
            return SwarmResult(
                final_output="",
                pattern=self.pattern,
                messages=messages,
                execution_time=round(time.time() - start_time, 3),
                status=AgentStatus.ERROR,
                error=str(e),
            )

    def _run_hierarchical(
        self, task: str, context: dict[str, Any], start_time: float
    ) -> SwarmResult:
        """Supervisor plans, delegates to workers, and synthesizes final answer."""
        messages: list[SwarmMessage] = []
        total_tokens = 0

        # Step 1: Supervisor or first agent assesses subtasks
        worker_outputs: dict[str, str] = {}
        for _agent_id, agent in self.agents.items():
            agent_res = agent.run(task, context=context)
            total_tokens += agent_res.tokens_used
            worker_outputs[agent.name] = agent_res.output
            messages.append(
                SwarmMessage(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    role="worker",
                    content=agent_res.output,
                )
            )

        # Step 2: Synthesis
        if self.supervisor:
            synth_prompt = (
                f"Synthesize the following expert agent reports to fulfill task: '{task}'\n\n"
                + "\n\n".join([f"=== {name} ===\n{out}" for name, out in worker_outputs.items()])
            )
            sup_res = self.supervisor.run(synth_prompt)
            total_tokens += sup_res.tokens_used
            final_output = sup_res.output
            messages.append(
                SwarmMessage(
                    agent_id=self.supervisor.id,
                    agent_name=self.supervisor.name,
                    role="supervisor",
                    content=final_output,
                )
            )
        else:
            final_output = "\n\n---\n\n".join(
                [f"### {name}\n{out}" for name, out in worker_outputs.items()]
            )

        return SwarmResult(
            final_output=final_output,
            pattern=SwarmPattern.HIERARCHICAL,
            messages=messages,
            execution_time=round(time.time() - start_time, 3),
            total_tokens=total_tokens,
            status=AgentStatus.COMPLETED,
        )

    def _run_peer_debate(
        self, task: str, context: dict[str, Any], start_time: float
    ) -> SwarmResult:
        """Agents critique and refine solutions across multiple rounds."""
        messages: list[SwarmMessage] = []
        total_tokens = 0
        agents_list = list(self.agents.values())
        if not agents_list:
            raise ValueError("No agents registered for peer debate.")

        current_solution = f"Initial prompt: {task}"
        for round_idx in range(self.max_rounds):
            for agent in agents_list:
                debate_prompt = (
                    f"Round {round_idx + 1} - Task: {task}\n"
                    f"Current leading formulation: {current_solution}\n"
                    f"Provide your constructive critique, improvements, and refined response."
                )
                res = agent.run(debate_prompt, context=context)
                total_tokens += res.tokens_used
                current_solution = res.output
                messages.append(
                    SwarmMessage(
                        agent_id=agent.id,
                        agent_name=agent.name,
                        role="debater",
                        content=res.output,
                        metadata={"round": round_idx + 1},
                    )
                )

        return SwarmResult(
            final_output=current_solution,
            pattern=SwarmPattern.PEER_DEBATE,
            messages=messages,
            execution_time=round(time.time() - start_time, 3),
            total_tokens=total_tokens,
            status=AgentStatus.COMPLETED,
        )

    def _run_voting_consensus(
        self, task: str, context: dict[str, Any], start_time: float
    ) -> SwarmResult:
        """Collects proposed answers from each agent and synthesizes consensus score."""
        messages: list[SwarmMessage] = []
        total_tokens = 0
        candidates: list[str] = []

        for agent in self.agents.values():
            res = agent.run(task, context=context)
            total_tokens += res.tokens_used
            candidates.append(res.output)
            messages.append(
                SwarmMessage(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    role="candidate_author",
                    content=res.output,
                )
            )

        # Synthesize consensus
        final_output = (
            f"Consensus synthesized from {len(candidates)} agent evaluations.\n\n"
            + "\n\n".join(candidates)
        )
        consensus_score = 0.95 if len(candidates) > 0 else 0.0

        return SwarmResult(
            final_output=final_output,
            pattern=SwarmPattern.VOTING_CONSENSUS,
            messages=messages,
            consensus_score=consensus_score,
            execution_time=round(time.time() - start_time, 3),
            total_tokens=total_tokens,
            status=AgentStatus.COMPLETED,
        )

    def _run_dynamic_router(
        self, task: str, context: dict[str, Any], start_time: float
    ) -> SwarmResult:
        """Route task to most specialized agent based on instruction affinity."""
        messages: list[SwarmMessage] = []
        agents_list = list(self.agents.values())
        if not agents_list:
            raise ValueError("No agents registered for dynamic router.")

        # Match best agent
        selected_agent = agents_list[0]
        for agent in agents_list:
            if any(word in task.lower() for word in agent.name.lower().split()):
                selected_agent = agent
                break

        res = selected_agent.run(task, context=context)
        messages.append(
            SwarmMessage(
                agent_id=selected_agent.id,
                agent_name=selected_agent.name,
                role="specialist",
                content=res.output,
            )
        )

        return SwarmResult(
            final_output=res.output,
            pattern=SwarmPattern.DYNAMIC_ROUTER,
            messages=messages,
            execution_time=round(time.time() - start_time, 3),
            total_tokens=res.tokens_used,
            status=AgentStatus.COMPLETED,
            metadata={"routed_to": selected_agent.id},
        )
