"""
Agent graph model for multi-agent orchestration.
"""

from dataclasses import dataclass, field
from typing import Any

from agent_factory.agents.agent import Agent


@dataclass
class AgentNode:
    """Node in agent graph representing an agent."""
    agent_id: str
    agent: Agent
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingEdge:
    """Edge in agent graph representing routing between agents."""
    from_agent: str
    to_agent: str
    condition: str | None = None  # Expression for conditional routing
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentGraph:
    """
    Graph of agents with routing edges.
    
    Example:
        >>> graph = AgentGraph(
        ...     nodes=[
        ...         AgentNode(agent_id="coordinator", agent=coordinator_agent),
        ...         AgentNode(agent_id="specialist", agent=specialist_agent),
        ...     ],
        ...     edges=[
        ...         RoutingEdge(from_agent="coordinator", to_agent="specialist"),
        ...     ],
        ...     entry_point="coordinator",
        ... )
    """
    nodes: list[AgentNode]
    edges: list[RoutingEdge]
    entry_point: str  # Starting agent ID
    
    def get_node(self, agent_id: str) -> AgentNode | None:
        """Get node by agent ID."""
        for node in self.nodes:
            if node.agent_id == agent_id:
                return node
        return None
    
    def get_outgoing_edges(self, agent_id: str) -> list[RoutingEdge]:
        """Get all outgoing edges from an agent."""
        return [edge for edge in self.edges if edge.from_agent == agent_id]
