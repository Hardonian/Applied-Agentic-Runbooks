"""
Tests for multi-agent orchestration.
"""

from agent_factory.agents.agent import Agent
from agent_factory.orchestration.graph import AgentGraph, AgentNode, RoutingEdge
from agent_factory.orchestration.router import AgentRouter


def test_agent_graph():
    """Test agent graph."""
    agent1 = Agent(id="agent1", name="Agent 1", instructions="Test")
    agent2 = Agent(id="agent2", name="Agent 2", instructions="Test")

    nodes = [
        AgentNode(agent_id="agent1", agent=agent1),
        AgentNode(agent_id="agent2", agent=agent2),
    ]

    edges = [
        RoutingEdge(from_agent="agent1", to_agent="agent2"),
    ]

    graph = AgentGraph(
        nodes=nodes,
        edges=edges,
        entry_point="agent1",
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.entry_point == "agent1"

    # Test get_node
    node = graph.get_node("agent1")
    assert node is not None
    assert node.agent_id == "agent1"

    # Test get_outgoing_edges
    outgoing = graph.get_outgoing_edges("agent1")
    assert len(outgoing) == 1
    assert outgoing[0].to_agent == "agent2"


def test_agent_router():
    """Test agent router."""
    agent1 = Agent(id="agent1", name="Agent 1", instructions="Test")
    agent2 = Agent(id="agent2", name="Agent 2", instructions="Test")

    graph = AgentGraph(
        nodes=[
            AgentNode(agent_id="agent1", agent=agent1),
            AgentNode(agent_id="agent2", agent=agent2),
        ],
        edges=[
            RoutingEdge(from_agent="agent1", to_agent="agent2"),
        ],
        entry_point="agent1",
    )

    router = AgentRouter()

    # Route from agent1
    next_agent = router.route({"message": "test"}, "agent1", graph)
    assert next_agent == "agent2"

    # Route from agent2 (no outgoing edges)
    next_agent = router.route({"message": "test"}, "agent2", graph)
    assert next_agent is None
