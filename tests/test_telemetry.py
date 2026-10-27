"""Tests for telemetry system."""

import uuid
from unittest.mock import Mock

import pytest

from agent_factory.telemetry.backends.base import TelemetryBackend
from agent_factory.telemetry.backends.sqlite import SQLiteTelemetryBackend
from agent_factory.telemetry.collector import TelemetryCollector, get_collector
from agent_factory.telemetry.model import (
    AgentRunEvent,
    BillingUsageEvent,
    BlueprintInstallEvent,
    ErrorEvent,
    EventType,
    TelemetryEvent,
    WorkflowRunEvent,
)


@pytest.mark.unit
def test_telemetry_event_creation():
    """Test creating a base telemetry event."""
    event = TelemetryEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.AGENT_RUN,
    )

    assert event.event_id is not None
    assert event.event_type == EventType.AGENT_RUN
    assert event.timestamp is not None
    assert event.metadata == {}


@pytest.mark.unit
def test_agent_run_event():
    """Test creating an agent run event."""
    event = AgentRunEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.AGENT_RUN,
        agent_id="test-agent",
        status="completed",
        tokens_used=100,
    )

    assert event.agent_id == "test-agent"
    assert event.status == "completed"
    assert event.tokens_used == 100
    assert event.event_type == EventType.AGENT_RUN

    # Test serialization
    data = event.to_dict()
    assert data["agent_id"] == "test-agent"
    assert data["status"] == "completed"


@pytest.mark.unit
def test_workflow_run_event():
    """Test creating a workflow run event."""
    event = WorkflowRunEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.WORKFLOW_RUN,
        workflow_id="test-workflow",
        steps_completed=5,
        steps_total=10,
    )

    assert event.workflow_id == "test-workflow"
    assert event.steps_completed == 5
    assert event.steps_total == 10


@pytest.mark.unit
def test_blueprint_install_event():
    """Test creating a blueprint install event."""
    event = BlueprintInstallEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.BLUEPRINT_INSTALL,
        blueprint_id="test-blueprint",
        install_type="install",
    )

    assert event.blueprint_id == "test-blueprint"
    assert event.install_type == "install"
    assert event.event_type == EventType.BLUEPRINT_INSTALL


@pytest.mark.unit
def test_error_event():
    """Test creating an error event."""
    event = ErrorEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.ERROR,
        error_type="ValueError",
        error_message="Test error",
    )

    assert event.error_type == "ValueError"
    assert event.error_message == "Test error"
    assert event.event_type == EventType.ERROR


@pytest.mark.unit
def test_billing_usage_event():
    """Test creating a billing usage event."""
    event = BillingUsageEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.BILLING_USAGE,
        billing_unit="agent_run",
        quantity=10.0,
        unit_price=0.01,
    )

    assert event.billing_unit == "agent_run"
    assert event.quantity == 10.0
    assert event.unit_price == 0.01
    assert event.total_cost == 0.1  # Auto-calculated


@pytest.mark.unit
def test_telemetry_collector_initialization():
    """Test telemetry collector initialization."""
    backend = SQLiteTelemetryBackend(":memory:")
    collector = TelemetryCollector(backend=backend)

    assert collector.backend == backend


@pytest.mark.unit
def test_collector_record_agent_run():
    """Test recording an agent run."""
    backend = Mock(spec=TelemetryBackend)
    collector = TelemetryCollector(backend=backend)

    collector.record_agent_run(
        agent_id="test-agent",
        tenant_id="tenant-123",
        status="completed",
        tokens_used=100,
    )

    assert backend.store_event.called
    call_args = backend.store_event.call_args[0][0]
    assert isinstance(call_args, AgentRunEvent)
    assert call_args.agent_id == "test-agent"


@pytest.mark.unit
def test_collector_record_workflow_run():
    """Test recording a workflow run."""
    backend = Mock(spec=TelemetryBackend)
    collector = TelemetryCollector(backend=backend)

    collector.record_workflow_run(
        workflow_id="test-workflow",
        status="completed",
        steps_completed=5,
    )

    assert backend.store_event.called
    call_args = backend.store_event.call_args[0][0]
    assert isinstance(call_args, WorkflowRunEvent)


@pytest.mark.unit
def test_collector_record_error():
    """Test recording an error."""
    backend = Mock(spec=TelemetryBackend)
    collector = TelemetryCollector(backend=backend)

    collector.record_error(
        error_type="ValueError",
        error_message="Test error",
    )

    assert backend.store_event.called
    call_args = backend.store_event.call_args[0][0]
    assert isinstance(call_args, ErrorEvent)


@pytest.mark.unit
def test_collector_query_events():
    """Test querying events."""
    backend = Mock(spec=TelemetryBackend)
    backend.query_events.return_value = []

    collector = TelemetryCollector(backend=backend)
    events = collector.query_events(tenant_id="tenant-123")

    assert backend.query_events.called
    assert events == []


@pytest.mark.unit
def test_get_collector_singleton():
    """Test get_collector returns singleton."""
    collector1 = get_collector()
    collector2 = get_collector()

    assert collector1 is collector2


@pytest.mark.unit
def test_sqlite_backend_store_and_query():
    """Test SQLite backend storage and querying."""
    backend = SQLiteTelemetryBackend(":memory:")

    event = AgentRunEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.AGENT_RUN,
        agent_id="test-agent",
        tenant_id="tenant-123",
    )

    backend.store_event(event)

    events = backend.query_events(tenant_id="tenant-123")
    assert len(events) == 1
    assert events[0].agent_id == "test-agent"


@pytest.mark.unit
def test_collector_silent_failure():
    """Test that collector fails silently on backend errors."""
    backend = Mock(spec=TelemetryBackend)
    backend.store_event.side_effect = Exception("Backend error")

    collector = TelemetryCollector(backend=backend)

    # Should not raise
    collector.record_agent_run(agent_id="test-agent")
