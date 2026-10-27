"""Tests for database models."""

import pytest

from agent_factory.database.models import (
    Agent as AgentModel,
)
from agent_factory.database.models import (
    AuditLog as AuditLogModel,
)
from agent_factory.database.models import (
    Blueprint as BlueprintModel,
)
from agent_factory.database.models import (
    Execution as ExecutionModel,
)
from agent_factory.database.models import (
    Tenant,
    User,
)
from agent_factory.database.models import (
    Workflow as WorkflowModel,
)


@pytest.mark.unit
def test_user_model():
    """Test User model structure."""
    user = User(
        id="user-1",
        email="test@example.com",
        hashed_password="hashed",
    )

    assert user.id == "user-1"
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.is_superuser is False


@pytest.mark.unit
def test_tenant_model():
    """Test Tenant model structure."""
    tenant = Tenant(
        id="tenant-1",
        name="Test Tenant",
        slug="test-tenant",
    )

    assert tenant.id == "tenant-1"
    assert tenant.name == "Test Tenant"
    assert tenant.slug == "test-tenant"
    assert tenant.plan == "free"
    assert tenant.is_active is True


@pytest.mark.unit
def test_agent_model():
    """Test Agent model structure."""
    agent = AgentModel(
        id="agent-1",
        name="Test Agent",
        instructions="Test instructions",
    )

    assert agent.id == "agent-1"
    assert agent.name == "Test Agent"
    assert agent.instructions == "Test instructions"
    assert agent.model == "gpt-4o"


@pytest.mark.unit
def test_workflow_model():
    """Test Workflow model structure."""
    workflow = WorkflowModel(
        id="workflow-1",
        name="Test Workflow",
        definition={"steps": []},
    )

    assert workflow.id == "workflow-1"
    assert workflow.name == "Test Workflow"
    assert isinstance(workflow.definition, dict)


@pytest.mark.unit
def test_blueprint_model():
    """Test Blueprint model structure."""
    blueprint = BlueprintModel(
        id="blueprint-1",
        name="Test Blueprint",
        version="1.0.0",
        description="Test description",
        definition={"agents": []},
    )

    assert blueprint.id == "blueprint-1"
    assert blueprint.name == "Test Blueprint"
    assert blueprint.version == "1.0.0"
    assert blueprint.pricing_model == "free"
    assert blueprint.price == 0.0


@pytest.mark.unit
def test_execution_model():
    """Test Execution model structure."""
    execution = ExecutionModel(
        id="exec-1",
        execution_type="agent",
        resource_id="agent-1",
        status="pending",
    )

    assert execution.id == "exec-1"
    assert execution.execution_type == "agent"
    assert execution.resource_id == "agent-1"
    assert execution.status == "pending"


@pytest.mark.unit
def test_audit_log_model():
    """Test AuditLog model structure."""
    audit_log = AuditLogModel(
        event_type="test_event",
        action="create",
        success=True,
    )

    assert audit_log.event_type == "test_event"
    assert audit_log.action == "create"
    assert audit_log.success is True
