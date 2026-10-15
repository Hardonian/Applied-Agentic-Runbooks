"""
Revenue tracking and analytics.

Provides methods to track and analyze revenue metrics.
"""

from datetime import datetime, timedelta

from agent_factory.telemetry.collector import TelemetryCollector, get_collector
from agent_factory.telemetry.model import EventType, RevenueEvent


class RevenueTracker:
    """
    Track and analyze revenue metrics.
    
    Example:
        >>> tracker = RevenueTracker()
        >>> mrr = tracker.get_mrr()
        >>> arr = tracker.get_arr()
    """
    
    def __init__(self, collector: TelemetryCollector | None = None):
        """
        Initialize revenue tracker.
        
        Args:
            collector: Telemetry collector instance
        """
        self.collector = collector or get_collector()
    
    def track_revenue(
        self,
        amount: float,
        tenant_id: str,
        user_id: str | None = None,
        revenue_type: str = "subscription",
        plan_id: str | None = None,
        subscription_id: str | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> None:
        """
        Track a revenue event.
        
        Args:
            amount: Revenue amount
            tenant_id: Tenant ID
            user_id: User ID (optional)
            revenue_type: Type of revenue (subscription, marketplace, services, enterprise)
            plan_id: Plan ID (optional)
            subscription_id: Subscription ID (optional)
            period_start: Period start date (optional)
            period_end: Period end date (optional)
        """
        import uuid
        
        event = RevenueEvent(
            event_id=str(uuid.uuid4()),
            amount=amount,
            currency="USD",
            revenue_type=revenue_type,
            plan_id=plan_id,
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
        )
        
        self.collector.record_event(event)
    
    def get_mrr(
        self,
        date: datetime | None = None,
    ) -> float:
        """
        Get Monthly Recurring Revenue (MRR).
        
        Args:
            date: Date to calculate MRR for (defaults to now)
            
        Returns:
            MRR amount
        """
        if not date:
            date = datetime.utcnow()
        
        # Get revenue events for current month
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = date
        
        events = self.collector.query_events(
            event_type=EventType.REVENUE.value,
            start_time=month_start,
            end_time=month_end,
            limit=10000,
        )
        
        # Sum subscription revenue
        mrr = sum(
            e.amount for e in events
            if isinstance(e, RevenueEvent) and e.revenue_type == "subscription"
        )
        
        return mrr
    
    def get_arr(self) -> float:
        """
        Get Annual Recurring Revenue (ARR).
        
        Returns:
            ARR amount (MRR × 12)
        """
        mrr = self.get_mrr()
        return mrr * 12
    
    def get_revenue_by_type(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, float]:
        """
        Get revenue breakdown by type.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping revenue type to amount
        """
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        events = self.collector.query_events(
            event_type=EventType.REVENUE.value,
            start_time=start_date,
            end_time=end_date,
            limit=10000,
        )
        
        revenue_by_type = {}
        for e in events:
            if isinstance(e, RevenueEvent):
                revenue_type = e.revenue_type
                revenue_by_type[revenue_type] = revenue_by_type.get(revenue_type, 0.0) + e.amount
        
        return revenue_by_type
    
    def get_revenue_by_plan(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, float]:
        """
        Get revenue breakdown by plan.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping plan ID to revenue amount
        """
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        events = self.collector.query_events(
            event_type=EventType.REVENUE.value,
            start_time=start_date,
            end_time=end_date,
            limit=10000,
        )
        
        revenue_by_plan = {}
        for e in events:
            if isinstance(e, RevenueEvent) and e.plan_id:
                plan_id = e.plan_id
                revenue_by_plan[plan_id] = revenue_by_plan.get(plan_id, 0.0) + e.amount
        
        return revenue_by_plan


# Global revenue tracker instance
_revenue_tracker: RevenueTracker | None = None


def get_revenue_tracker() -> RevenueTracker:
    """
    Get global revenue tracker instance.
    
    Returns:
        Revenue tracker
    """
    global _revenue_tracker
    if _revenue_tracker is None:
        _revenue_tracker = RevenueTracker()
    return _revenue_tracker
