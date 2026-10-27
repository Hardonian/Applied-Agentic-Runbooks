"""
Telemetry collector for capturing and storing telemetry events.
"""

import uuid
from datetime import datetime

from agent_factory.telemetry.backends.base import TelemetryBackend
from agent_factory.telemetry.backends.sqlite import SQLiteTelemetryBackend
from agent_factory.telemetry.model import EventType, TelemetryEvent


class TelemetryCollector:
    """
    Central telemetry collector for Agent Factory Platform.

    Collects and stores telemetry events from various sources:
    - Agent runs
    - Workflow runs
    - Blueprint installations
    - Errors
    - Billing usage

    Example:
        >>> collector = TelemetryCollector()
        >>> collector.record_agent_run(
        ...     agent_id="my-agent",
        ...     tenant_id="tenant-123",
        ...     status="completed",
        ...     execution_time=1.5,
        ...     tokens_used=100
        ... )
    """

    def __init__(self, backend: TelemetryBackend | None = None):
        """
        Initialize telemetry collector.

        Args:
            backend: Telemetry storage backend (defaults to SQLite)
        """
        self.backend = backend or SQLiteTelemetryBackend()

    def record_event(self, event: TelemetryEvent) -> None:
        """
        Record a telemetry event.

        Args:
            event: Telemetry event to record
        """
        if not event.event_id:
            event.event_id = str(uuid.uuid4())

        try:
            self.backend.store_event(event)
        except (
            Exception
        ):  # nosec B110 -- telemetry write is best-effort by design (comment: never break main execution)
            # Silently fail telemetry to avoid breaking main execution
            # In production, log to error tracking system
            pass

    def record_agent_run(
        self,
        agent_id: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        agent_name: str | None = None,
        session_id: str | None = None,
        status: str = "completed",
        execution_time: float = 0.0,
        tokens_used: int = 0,
        cost_estimate: float = 0.0,
        input_length: int = 0,
        output_length: int = 0,
        metadata: dict | None = None,
    ) -> None:
        """
        Record an agent run event.

        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            user_id: User ID
            project_id: Project/App ID
            agent_name: Agent name
            session_id: Session ID
            status: Execution status
            execution_time: Execution time in seconds
            tokens_used: Tokens used
            cost_estimate: Estimated cost
            input_length: Input text length
            output_length: Output text length
            metadata: Additional metadata
        """
        from agent_factory.telemetry.model import AgentRunEvent

        event = AgentRunEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.AGENT_RUN,
            agent_id=agent_id,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            agent_name=agent_name,
            session_id=session_id,
            status=status,
            execution_time=execution_time,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
            input_length=input_length,
            output_length=output_length,
            metadata=metadata or {},
        )

        self.record_event(event)

    def record_workflow_run(
        self,
        workflow_id: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        workflow_name: str | None = None,
        status: str = "completed",
        execution_time: float = 0.0,
        steps_completed: int = 0,
        steps_total: int = 0,
        tokens_used: int = 0,
        cost_estimate: float = 0.0,
        metadata: dict | None = None,
    ) -> None:
        """
        Record a workflow run event.

        Args:
            workflow_id: Workflow ID
            tenant_id: Tenant ID
            user_id: User ID
            project_id: Project/App ID
            workflow_name: Workflow name
            status: Execution status
            execution_time: Execution time in seconds
            steps_completed: Number of steps completed
            steps_total: Total number of steps
            tokens_used: Tokens used
            cost_estimate: Estimated cost
            metadata: Additional metadata
        """
        from agent_factory.telemetry.model import WorkflowRunEvent

        event = WorkflowRunEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.WORKFLOW_RUN,
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            workflow_name=workflow_name,
            status=status,
            execution_time=execution_time,
            steps_completed=steps_completed,
            steps_total=steps_total,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
            metadata=metadata or {},
        )

        self.record_event(event)

    def record_blueprint_install(
        self,
        blueprint_id: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        blueprint_name: str | None = None,
        blueprint_version: str | None = None,
        install_type: str = "install",
        metadata: dict | None = None,
    ) -> None:
        """
        Record a blueprint installation event.

        Args:
            blueprint_id: Blueprint ID
            tenant_id: Tenant ID
            user_id: User ID
            project_id: Project/App ID
            blueprint_name: Blueprint name
            blueprint_version: Blueprint version
            install_type: install or uninstall
            metadata: Additional metadata
        """
        from agent_factory.telemetry.model import BlueprintInstallEvent

        event = BlueprintInstallEvent(
            event_id=str(uuid.uuid4()),
            event_type=(
                EventType.BLUEPRINT_INSTALL
                if install_type == "install"
                else EventType.BLUEPRINT_UNINSTALL
            ),
            blueprint_id=blueprint_id,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            blueprint_name=blueprint_name,
            blueprint_version=blueprint_version,
            install_type=install_type,
            metadata=metadata or {},
        )

        self.record_event(event)

    def record_error(
        self,
        error_type: str,
        error_message: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        stack_trace: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        Record an error event.

        Args:
            error_type: Error type/class name
            error_message: Error message
            tenant_id: Tenant ID
            user_id: User ID
            project_id: Project/App ID
            resource_type: Resource type (agent, workflow, etc.)
            resource_id: Resource ID
            stack_trace: Stack trace
            metadata: Additional metadata
        """
        from agent_factory.telemetry.model import ErrorEvent

        event = ErrorEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ERROR,
            error_type=error_type,
            error_message=error_message,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            stack_trace=stack_trace,
            metadata=metadata or {},
        )

        self.record_event(event)

    def record_billing_usage(
        self,
        billing_unit: str,
        quantity: float,
        tenant_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        unit_price: float = 0.0,
        total_cost: float = 0.0,
        currency: str = "USD",
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        Record a billing usage event.

        Args:
            billing_unit: Billing unit (agent_run, workflow_run, token, etc.)
            quantity: Quantity consumed
            tenant_id: Tenant ID
            user_id: User ID
            project_id: Project/App ID
            unit_price: Price per unit
            total_cost: Total cost
            currency: Currency code
            period_start: Period start time
            period_end: Period end time
            metadata: Additional metadata
        """
        from agent_factory.telemetry.model import BillingUsageEvent

        event = BillingUsageEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.BILLING_USAGE,
            billing_unit=billing_unit,
            quantity=quantity,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            unit_price=unit_price,
            total_cost=total_cost,
            currency=currency,
            period_start=period_start,
            period_end=period_end,
            metadata=metadata or {},
        )

        self.record_event(event)

    def query_events(
        self,
        event_type: str | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[TelemetryEvent]:
        """
        Query telemetry events.

        Args:
            event_type: Filter by event type
            tenant_id: Filter by tenant ID
            user_id: Filter by user ID
            project_id: Filter by project ID
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of results

        Returns:
            List of telemetry events
        """
        return self.backend.query_events(
            event_type=event_type,
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )


# Global collector instance
_collector: TelemetryCollector | None = None


def get_collector() -> TelemetryCollector:
    """
    Get global telemetry collector instance.

    Returns:
        Telemetry collector
    """
    global _collector
    if _collector is None:
        _collector = TelemetryCollector()
    return _collector
