"""
Message routing logic for multi-agent orchestration.
"""

from typing import Any

from agent_factory.orchestration.graph import AgentGraph
from agent_factory.utils.safe_evaluator import SafeEvaluator


class AgentRouter:
    """Route messages between agents in a graph."""

    def __init__(self):
        """Initialize router with safe evaluator."""
        self.evaluator = SafeEvaluator()

    def route(
        self,
        message: dict[str, Any],
        current_agent_id: str,
        graph: AgentGraph,
    ) -> str | None:
        """
        Determine next agent to route to.

        Args:
            message: Current message/context
            current_agent_id: Current agent ID
            graph: Agent graph

        Returns:
            Next agent ID, or None if routing should stop
        """
        outgoing_edges = graph.get_outgoing_edges(current_agent_id)

        if not outgoing_edges:
            return None

        # Evaluate conditions for each edge
        for edge in outgoing_edges:
            if not edge.condition:
                # No condition, route immediately
                return edge.to_agent

            # Evaluate condition expression with message context
            try:
                # Build evaluation context from message
                context = {
                    "message": message,
                    "current_agent": current_agent_id,
                    **message,  # Flatten message keys for easier access
                }

                # Evaluate condition
                result = self.evaluator.evaluate(edge.condition, context)

                # If condition is truthy, route to this agent
                if result:
                    return edge.to_agent
            except Exception:
                # If evaluation fails, skip this edge
                continue

        # No matching edge found
        return None
