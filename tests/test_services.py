"""
Tests for service layer.
"""

from agent_factory.services.agent_service import AgentService
from agent_factory.services.blueprint_service import BlueprintService
from agent_factory.services.execution_service import ExecutionService
from agent_factory.services.workflow_service import WorkflowService


def test_agent_service_create():
    """Test agent service create."""
    service = AgentService()
    
    agent_data = {
        "id": "test-agent",
        "name": "Test Agent",
        "instructions": "You are a test agent",
    }
    
    agent = service.create_agent(agent_data)
    assert agent.id == "test-agent"
    assert agent.name == "Test Agent"


def test_agent_service_get():
    """Test agent service get."""
    service = AgentService()
    
    agent_data = {
        "id": "test-agent",
        "name": "Test Agent",
        "instructions": "You are a test agent",
    }
    
    service.create_agent(agent_data)
    agent = service.get_agent("test-agent")
    
    assert agent is not None
    assert agent.id == "test-agent"


def test_agent_service_list():
    """Test agent service list."""
    service = AgentService()
    
    agent_data = {
        "id": "test-agent",
        "name": "Test Agent",
        "instructions": "You are a test agent",
    }
    
    service.create_agent(agent_data)
    agents = service.list_agents()
    
    assert "test-agent" in agents


def test_agent_service_update():
    """Test agent service update."""
    service = AgentService()
    
    agent_data = {
        "id": "test-agent",
        "name": "Test Agent",
        "instructions": "You are a test agent",
    }
    
    service.create_agent(agent_data)
    
    updated = service.update_agent("test-agent", {"name": "Updated Agent"})
    assert updated is not None
    assert updated.name == "Updated Agent"


def test_agent_service_delete():
    """Test agent service delete."""
    service = AgentService()
    
    agent_data = {
        "id": "test-agent",
        "name": "Test Agent",
        "instructions": "You are a test agent",
    }
    
    service.create_agent(agent_data)
    deleted = service.delete_agent("test-agent")
    
    assert deleted is True
    assert service.get_agent("test-agent") is None


def test_workflow_service_create():
    """Test workflow service create."""
    service = WorkflowService()
    
    workflow_data = {
        "id": "test-workflow",
        "name": "Test Workflow",
        "steps": [],
    }
    
    workflow = service.create_workflow(workflow_data)
    assert workflow.id == "test-workflow"


def test_blueprint_service_load():
    """Test blueprint service load."""
    service = BlueprintService()
    
    # Test loading blueprint (would need actual blueprint file)
    # This is a placeholder test
    assert service is not None


def test_execution_service_get():
    """Test execution service get."""
    service = ExecutionService()
    
    # Test getting execution (would need actual execution)
    executions = service.list_executions()
    assert isinstance(executions, list)
