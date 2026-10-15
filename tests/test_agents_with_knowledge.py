"""
Tests for agents with knowledge packs.
"""


from agent_factory.agents.agent import Agent
from agent_factory.knowledge.model import KnowledgePack


def test_agent_with_knowledge_pack():
    """Test agent with knowledge pack."""
    pack = KnowledgePack(
        id="test-pack",
        name="Test Pack",
        description="Test",
        domain="test",
    )
    
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
        knowledge_packs=[pack],
    )
    
    assert len(agent.knowledge_packs) == 1
    assert agent.knowledge_packs[0].id == "test-pack"


def test_attach_knowledge_pack():
    """Test attaching knowledge pack to agent."""
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )
    
    pack = KnowledgePack(
        id="test-pack",
        name="Test Pack",
        description="Test",
        domain="test",
    )
    
    agent.attach_knowledge_pack(pack)
    
    assert len(agent.knowledge_packs) == 1
    assert agent.knowledge_packs[0].id == "test-pack"
    
    # Attach again (should not duplicate)
    agent.attach_knowledge_pack(pack)
    assert len(agent.knowledge_packs) == 1
