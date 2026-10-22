"""
Analytics engine for computing growth metrics and insights.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from agent_factory.telemetry.collector import TelemetryCollector, get_collector
from agent_factory.telemetry.model import EventType


class AnalyticsEngine:
    """
    Analytics engine for computing growth metrics and insights.

    Computes metrics like:
    - DAU/WAU/MAU (Daily/Weekly/Monthly Active Users)
    - Active agents/workflows per tenant
    - Blueprint installs per type
    - Conversion funnel metrics
    - Token usage & costs per tenant

    Example:
        >>> analytics = AnalyticsEngine()
        >>> metrics = analytics.get_growth_summary()
        >>> print(metrics["dau"])
    """

    def __init__(self, collector: TelemetryCollector | None = None):
        """
        Initialize analytics engine.

        Args:
            collector: Telemetry collector instance
        """
        self.collector = collector or get_collector()

    def get_growth_summary(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get overall growth summary metrics.

        Args:
            start_date: Start date for metrics (defaults to 30 days ago)
            end_date: End date for metrics (defaults to now)

        Returns:
            Dictionary with growth metrics
        """
        if not end_date:
            end_date = datetime.utcnow()

        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get all events in the period
        events = self.collector.query_events(
            start_time=start_date,
            end_time=end_date,
            limit=10000,  # Large limit for aggregation
        )

        # Compute metrics
        metrics = {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "dau": self._compute_dau(events, end_date),
            "wau": self._compute_wau(events, end_date),
            "mau": self._compute_mau(events, end_date),
            "total_tenants": self._count_unique_tenants(events),
            "total_users": self._count_unique_users(events),
            "total_agent_runs": self._count_events(events, EventType.AGENT_RUN.value),
            "total_workflow_runs": self._count_events(events, EventType.WORKFLOW_RUN.value),
            "total_blueprint_installs": self._count_events(
                events, EventType.BLUEPRINT_INSTALL.value
            ),
            "total_errors": self._count_events(events, EventType.ERROR.value),
            "total_tokens_used": self._sum_tokens(events),
            "total_cost_estimate": self._sum_costs(events),
            "active_agents": self._count_unique_agents(events),
            "active_workflows": self._count_unique_workflows(events),
            "blueprint_installs_by_type": self._blueprint_installs_by_type(events),
        }

        return metrics

    def get_tenant_metrics(
        self,
        tenant_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get metrics for a specific tenant.

        Args:
            tenant_id: Tenant ID
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            Dictionary with tenant-specific metrics
        """
        if not end_date:
            end_date = datetime.utcnow()

        if not start_date:
            start_date = end_date - timedelta(days=30)

        events = self.collector.query_events(
            tenant_id=tenant_id,
            start_time=start_date,
            end_time=end_date,
            limit=10000,
        )

        metrics = {
            "tenant_id": tenant_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_users": self._count_unique_users(events),
            "total_agent_runs": self._count_events(events, EventType.AGENT_RUN.value),
            "total_workflow_runs": self._count_events(events, EventType.WORKFLOW_RUN.value),
            "total_blueprint_installs": self._count_events(
                events, EventType.BLUEPRINT_INSTALL.value
            ),
            "total_errors": self._count_events(events, EventType.ERROR.value),
            "total_tokens_used": self._sum_tokens(events),
            "total_cost_estimate": self._sum_costs(events),
            "active_agents": self._count_unique_agents(events),
            "active_workflows": self._count_unique_workflows(events),
            "agent_runs_by_agent": self._agent_runs_by_agent(events),
            "workflow_runs_by_workflow": self._workflow_runs_by_workflow(events),
            "error_rate": self._compute_error_rate(events),
        }

        return metrics

    def get_conversion_funnel(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Compute conversion funnel metrics.

        User-focused funnel: Visitor → Signup → Activated → Retained → Paying

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Conversion funnel metrics
        """
        if not end_date:
            end_date = datetime.utcnow()

        if not start_date:
            start_date = end_date - timedelta(days=30)

        events = self.collector.query_events(
            start_time=start_date,
            end_time=end_date,
            limit=10000,
        )

        from agent_factory.telemetry.model import (
            RevenueEvent,
            TenantEvent,
            UserSignupEvent,
        )

        # Count funnel stages
        signups = self._count_events(events, EventType.USER_SIGNUP.value)
        activated = self._count_events(events, EventType.USER_ACTIVATED.value)

        # Retained = users active in last 7 days who signed up in period
        signup_user_ids = {
            e.user_id for e in events if isinstance(e, (TenantEvent, UserSignupEvent)) and e.user_id
        }

        # Check retention (active in last 7 days)
        retention_start = end_date - timedelta(days=7)
        retention_events = self.collector.query_events(
            start_time=retention_start,
            end_time=end_date,
            limit=10000,
        )
        retained_user_ids = {e.user_id for e in retention_events if e.user_id in signup_user_ids}
        retained = len(retained_user_ids)

        # Paying = users with revenue events
        paying_user_ids = {e.user_id for e in events if isinstance(e, RevenueEvent) and e.user_id}
        paying = len(paying_user_ids)

        # Also track product funnel (notebook → agent → blueprint → project)
        notebook_conversions = self._count_events(events, EventType.NOTEBOOK_CONVERTED.value)
        agents_created = self._count_unique_agents(events)
        blueprints_installed = self._count_events(events, EventType.BLUEPRINT_INSTALL.value)
        projects_created = self._count_events(events, EventType.PROJECT_CREATED.value)

        funnel = {
            # User-focused funnel
            "user_funnel": {
                "signups": signups,
                "activated": activated,
                "retained": retained,
                "paying": paying,
                "conversion_rates": {
                    "signup_to_activated": activated / signups if signups > 0 else 0.0,
                    "activated_to_retained": retained / activated if activated > 0 else 0.0,
                    "retained_to_paying": paying / retained if retained > 0 else 0.0,
                    "signup_to_paying": paying / signups if signups > 0 else 0.0,
                },
            },
            # Product funnel (legacy)
            "product_funnel": {
                "notebooks_converted": notebook_conversions,
                "agents_created": agents_created,
                "blueprints_installed": blueprints_installed,
                "projects_created": projects_created,
                "conversion_rates": {
                    "notebook_to_agent": (
                        agents_created / notebook_conversions if notebook_conversions > 0 else 0.0
                    ),
                    "agent_to_blueprint": (
                        blueprints_installed / agents_created if agents_created > 0 else 0.0
                    ),
                    "blueprint_to_project": (
                        projects_created / blueprints_installed if blueprints_installed > 0 else 0.0
                    ),
                },
            },
        }

        return funnel

    def _compute_dau(self, events: list, date: datetime) -> int:
        """Compute Daily Active Users."""
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_events = [e for e in events if day_start <= e.timestamp < day_end and e.user_id]

        return len(set(e.user_id for e in day_events))

    def _compute_wau(self, events: list, date: datetime) -> int:
        """Compute Weekly Active Users."""
        week_start = date - timedelta(days=7)

        week_events = [e for e in events if week_start <= e.timestamp <= date and e.user_id]

        return len(set(e.user_id for e in week_events))

    def _compute_mau(self, events: list, date: datetime) -> int:
        """Compute Monthly Active Users."""
        month_start = date - timedelta(days=30)

        month_events = [e for e in events if month_start <= e.timestamp <= date and e.user_id]

        return len(set(e.user_id for e in month_events))

    def _count_unique_tenants(self, events: list) -> int:
        """Count unique tenants."""
        tenant_ids = {e.tenant_id for e in events if e.tenant_id}
        return len(tenant_ids)

    def _count_unique_users(self, events: list) -> int:
        """Count unique users."""
        user_ids = {e.user_id for e in events if e.user_id}
        return len(user_ids)

    def _count_events(self, events: list, event_type: str) -> int:
        """Count events of a specific type."""
        return sum(1 for e in events if e.event_type.value == event_type)

    def _count_unique_agents(self, events: list) -> int:
        """Count unique agents."""
        from agent_factory.telemetry.model import AgentRunEvent

        agent_ids = {e.agent_id for e in events if isinstance(e, AgentRunEvent) and e.agent_id}
        return len(agent_ids)

    def _count_unique_workflows(self, events: list) -> int:
        """Count unique workflows."""
        from agent_factory.telemetry.model import WorkflowRunEvent

        workflow_ids = {
            e.workflow_id for e in events if isinstance(e, WorkflowRunEvent) and e.workflow_id
        }
        return len(workflow_ids)

    def _sum_tokens(self, events: list) -> int:
        """Sum tokens used across events."""
        from agent_factory.telemetry.model import AgentRunEvent, WorkflowRunEvent

        total = 0
        for e in events:
            if isinstance(e, AgentRunEvent):
                total += e.tokens_used
            elif isinstance(e, WorkflowRunEvent):
                total += e.tokens_used

        return total

    def _sum_costs(self, events: list) -> float:
        """Sum cost estimates across events."""
        from agent_factory.telemetry.model import AgentRunEvent, WorkflowRunEvent

        total = 0.0
        for e in events:
            if isinstance(e, AgentRunEvent):
                total += e.cost_estimate
            elif isinstance(e, WorkflowRunEvent):
                total += e.cost_estimate

        return total

    def _blueprint_installs_by_type(self, events: list) -> dict[str, int]:
        """Count blueprint installs by blueprint ID."""
        from agent_factory.telemetry.model import BlueprintInstallEvent

        counts = defaultdict(int)
        for e in events:
            if isinstance(e, BlueprintInstallEvent) and e.install_type == "install":
                blueprint_id = e.blueprint_id or "unknown"
                counts[blueprint_id] += 1

        return dict(counts)

    def _agent_runs_by_agent(self, events: list) -> dict[str, int]:
        """Count agent runs by agent ID."""
        from agent_factory.telemetry.model import AgentRunEvent

        counts = defaultdict(int)
        for e in events:
            if isinstance(e, AgentRunEvent):
                agent_id = e.agent_id or "unknown"
                counts[agent_id] += 1

        return dict(counts)

    def _workflow_runs_by_workflow(self, events: list) -> dict[str, int]:
        """Count workflow runs by workflow ID."""
        from agent_factory.telemetry.model import WorkflowRunEvent

        counts = defaultdict(int)
        for e in events:
            if isinstance(e, WorkflowRunEvent):
                workflow_id = e.workflow_id or "unknown"
                counts[workflow_id] += 1

        return dict(counts)

    def _compute_error_rate(self, events: list) -> float:
        """Compute error rate (errors / total events)."""
        total_events = len(events)
        if total_events == 0:
            return 0.0

        error_count = self._count_events(events, EventType.ERROR.value)
        return error_count / total_events

    def get_channel_attribution(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get user acquisition by channel.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Channel attribution metrics
        """
        if not end_date:
            end_date = datetime.utcnow()

        if not start_date:
            start_date = end_date - timedelta(days=30)

        events = self.collector.query_events(
            event_type=EventType.TENANT_CREATED.value,
            start_time=start_date,
            end_time=end_date,
            limit=10000,
        )

        from agent_factory.telemetry.model import TenantEvent

        channel_counts = defaultdict(int)
        channel_conversions = defaultdict(int)  # To paid

        for e in events:
            if isinstance(e, TenantEvent) and e.signup_source:
                channel = e.signup_source
                channel_counts[channel] += 1
                # Count conversions to paid (if plan is not free)
                if e.plan and e.plan != "free":
                    channel_conversions[channel] += 1

        # Calculate conversion rates
        channel_metrics = {}
        for channel, count in channel_counts.items():
            conversions = channel_conversions.get(channel, 0)
            channel_metrics[channel] = {
                "signups": count,
                "paid_conversions": conversions,
                "conversion_rate": conversions / count if count > 0 else 0.0,
            }

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "channels": dict(channel_metrics),
            "total_signups": sum(channel_counts.values()),
        }

    def get_retention_cohort(
        self,
        cohort_date: datetime,
        days: list[int] | None = None,
    ) -> dict[int, float]:
        """
        Compute retention for a cohort.

        Args:
            cohort_date: Date when cohort signed up
            days: List of days to check retention (e.g., [1, 7, 30])

        Returns:
            Dictionary mapping days to retention rate
        """
        if days is None:
            days = [1, 7, 30]
        # Get users who signed up on cohort_date
        signup_events = self.collector.query_events(
            event_type=EventType.TENANT_CREATED.value,
            start_time=cohort_date.replace(hour=0, minute=0, second=0, microsecond=0),
            end_time=cohort_date.replace(hour=23, minute=59, second=59, microsecond=999999),
            limit=10000,
        )

        from agent_factory.telemetry.model import TenantEvent

        cohort_user_ids = {
            e.user_id for e in signup_events if isinstance(e, TenantEvent) and e.user_id
        }

        if not cohort_user_ids:
            return {day: 0.0 for day in days}

        cohort_size = len(cohort_user_ids)

        # Check retention at each day
        retention = {}
        for day in days:
            check_date = cohort_date + timedelta(days=day)
            check_start = check_date.replace(hour=0, minute=0, second=0, microsecond=0)
            check_end = check_start + timedelta(days=1)

            # Get active users from cohort on check_date
            active_events = self.collector.query_events(
                start_time=check_start,
                end_time=check_end,
                limit=10000,
            )

            active_user_ids = {e.user_id for e in active_events if e.user_id in cohort_user_ids}

            retention[day] = len(active_user_ids) / cohort_size if cohort_size > 0 else 0.0

        return retention

    def get_growth_rate(
        self,
        metric: str,  # "users", "tenants", "revenue", "agent_runs"
        period: str = "month",  # "week", "month"
    ) -> dict[str, float]:
        """
        Compute growth rate for a metric.

        Args:
            metric: Metric to track ("users", "tenants", "revenue", "agent_runs")
            period: Period for comparison ("week", "month")

        Returns:
            Dictionary with growth rate and values
        """
        end_date = datetime.utcnow()

        if period == "week":
            delta = timedelta(days=7)
        else:  # month
            delta = timedelta(days=30)

        current_start = end_date - delta
        previous_start = current_start - delta
        previous_end = current_start

        # Get current period value
        current_events = self.collector.query_events(
            start_time=current_start,
            end_time=end_date,
            limit=10000,
        )

        # Get previous period value
        previous_events = self.collector.query_events(
            start_time=previous_start,
            end_time=previous_end,
            limit=10000,
        )

        # Calculate metric values
        if metric == "users":
            current_value = self._count_unique_users(current_events)
            previous_value = self._count_unique_users(previous_events)
        elif metric == "tenants":
            current_value = self._count_unique_tenants(current_events)
            previous_value = self._count_unique_tenants(previous_events)
        elif metric == "agent_runs":
            current_value = self._count_events(current_events, EventType.AGENT_RUN.value)
            previous_value = self._count_events(previous_events, EventType.AGENT_RUN.value)
        elif metric == "revenue":
            from agent_factory.telemetry.model import RevenueEvent

            current_value = sum(e.amount for e in current_events if isinstance(e, RevenueEvent))
            previous_value = sum(e.amount for e in previous_events if isinstance(e, RevenueEvent))
        else:
            current_value = 0
            previous_value = 0

        # Calculate growth rate
        if previous_value == 0:
            growth_rate = float("inf") if current_value > 0 else 0.0
        else:
            growth_rate = ((current_value - previous_value) / previous_value) * 100

        return {
            "metric": metric,
            "period": period,
            "current_value": current_value,
            "previous_value": previous_value,
            "growth_rate": growth_rate,
            "current_period_start": current_start.isoformat(),
            "current_period_end": end_date.isoformat(),
            "previous_period_start": previous_start.isoformat(),
            "previous_period_end": previous_end.isoformat(),
        }


# Global analytics instance
_analytics: AnalyticsEngine | None = None


def get_analytics() -> AnalyticsEngine:
    """
    Get global analytics engine instance.

    Returns:
        Analytics engine
    """
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsEngine()
    return _analytics
