"""
Multi-agent orchestration executor.
"""

from typing import Any

from agent_factory.orchestration.graph import AgentGraph
from agent_factory.orchestration.router import AgentRouter
from agent_factory.promptlog import SQLiteStorage
from agent_factory.promptlog.model import Run as RunModel


class OrchestrationExecutor:
    """Execute multi-agent orchestration flows."""

    def __init__(self, storage: SQLiteStorage | None = None):
        """
        Initialize executor.

        Args:
            storage: Optional prompt log storage
        """
        self.router = AgentRouter()
        self.storage = storage

    def execute(
        self,
        graph: AgentGraph,
        inputs: dict[str, Any],
        max_steps: int = 10,
    ) -> dict[str, Any]:
        """
        Execute multi-agent flow.

        Args:
            graph: Agent graph
            inputs: Initial inputs
            max_steps: Maximum number of routing steps

        Returns:
            Final outputs
        """
        current_agent_id = graph.entry_point
        current_message = inputs
        step_count = 0

        while current_agent_id and step_count < max_steps:
            # Get current agent
            node = graph.get_node(current_agent_id)
            if not node:
                break

            # Execute agent (placeholder - would use actual runtime)
            # result = node.agent.run(current_message)
            # For now, placeholder
            result = {"output": "placeholder"}

            # Log execution
            if self.storage:
                run = RunModel(
                    run_id=f"orchestration-{step_count}",
                    agent_id=current_agent_id,
                    inputs=current_message,
                    outputs=result,
                    status="success",
                )
                self.storage.save_run(run)

            # Route to next agent
            next_agent_id = self.router.route(result, current_agent_id, graph)

            if not next_agent_id:
                break

            current_agent_id = next_agent_id
            current_message = result
            step_count += 1

        return current_message
