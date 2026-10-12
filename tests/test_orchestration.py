"""
Tests for multi-agent orchestration.
"""

import pytest

from agent_factory.orchestration.graph import AgentGraph, AgentNode, RoutingEdge
from agent_factory.orchestration.router import AgentRouter
from agent_factory.orchestration.executor import OrchestrationExecutor
from agent_factory.agents.agent import Agent
from agent_factory.agents.agent import AgentResult, AgentStatus


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


def test_executor_runs_agents_and_returns_real_output():
    class FakeAgent:
        def __init__(self, response):
            self.response = response

        def run(self, _input, context=None):
            return AgentResult(output=self.response, status=AgentStatus.COMPLETED)

    graph = AgentGraph(
        nodes=[
            AgentNode(agent_id="first", agent=FakeAgent("first output")),
            AgentNode(agent_id="second", agent=FakeAgent("final output")),
        ],
        edges=[RoutingEdge(from_agent="first", to_agent="second")],
        entry_point="first",
    )

    result = OrchestrationExecutor().execute(graph, {"input_text": "hello"})

    assert result["output"] == "final output"
    assert result["status"] == "completed"
    assert [step["agent_id"] for step in result["steps"]] == ["first", "second"]


def test_executor_stops_on_agent_error():
    class FailingAgent:
        def run(self, _input, context=None):
            return AgentResult(output="", status=AgentStatus.ERROR, error="provider failed")

    graph = AgentGraph(
        nodes=[AgentNode(agent_id="broken", agent=FailingAgent())],
        edges=[],
        entry_point="broken",
    )

    result = OrchestrationExecutor().execute(graph, {"input_text": "hello"})
    assert result["status"] == "error"
    assert result["error"] == "provider failed"
