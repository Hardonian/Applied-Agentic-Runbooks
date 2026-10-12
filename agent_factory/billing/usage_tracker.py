"""
Usage tracker for billing and quota management.
"""

import uuid
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from agent_factory.telemetry.collector import get_collector
from agent_factory.telemetry.model import BillingUsageEvent
from agent_factory.database.session import get_db
from agent_factory.database.models import UsageRecord as UsageRecordModel, Tenant


class UsageTracker:
    """
    Tracks usage for billing purposes.
    
    Consumes telemetry events and aggregates usage by tenant.
    
    Example:
        >>> tracker = UsageTracker()
        >>> tracker.record_agent_run(tenant_id="t1", tokens_used=100)
        >>> summary = tracker.get_usage_summary("t1")
    """
    
    def __init__(self):
        """Initialize usage tracker."""
        self.collector = get_collector()
    
    def record_agent_run(
        self,
        tenant_id: str,
        tokens_used: int = 0,
        cost_estimate: float = 0.0,
        project_id: Optional[str] = None,
    ) -> None:
        """
        Record an agent run for billing.
        
        Args:
            tenant_id: Tenant ID
            tokens_used: Tokens used
            cost_estimate: Cost estimate
            project_id: Optional project ID
        """
        # Meter tokens separately but do not charge the same estimated cost
        # twice.  The run event is the billable execution record.
        if tokens_used > 0:
            self.collector.record_billing_usage(
                billing_unit="token",
                quantity=float(tokens_used),
                tenant_id=tenant_id,
                project_id=project_id,
                unit_price=0.0,  # Will be calculated based on plan
                total_cost=0.0,
            )
        self.collector.record_billing_usage(
            billing_unit="agent_run",
            quantity=1.0,
            tenant_id=tenant_id,
            project_id=project_id,
            unit_price=0.0,  # Will be calculated based on plan
            total_cost=cost_estimate,
        )
    
    def record_workflow_run(
        self,
        tenant_id: str,
        tokens_used: int = 0,
        cost_estimate: float = 0.0,
        project_id: Optional[str] = None,
    ) -> None:
        """
        Record a workflow run for billing.
        
        Args:
            tenant_id: Tenant ID
            tokens_used: Tokens used
            cost_estimate: Cost estimate
            project_id: Optional project ID
        """
        if tokens_used > 0:
            self.collector.record_billing_usage(
                billing_unit="token",
                quantity=float(tokens_used),
                tenant_id=tenant_id,
                project_id=project_id,
                unit_price=0.0,
                total_cost=0.0,
            )
        self.collector.record_billing_usage(
            billing_unit="workflow_run",
            quantity=1.0,
            tenant_id=tenant_id,
            project_id=project_id,
            unit_price=0.0,
            total_cost=cost_estimate,
        )
    
    def get_usage_summary(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get usage summary for a tenant.
        
        Args:
            tenant_id: Tenant ID
            start_date: Start date (defaults to start of current billing period)
            end_date: End date (defaults to now)
            
        Returns:
            Usage summary dictionary
        """
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            # Default to start of current month
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Query billing events from telemetry
        events = self.collector.query_events(
            event_type="billing_usage",
            tenant_id=tenant_id,
            start_time=start_date,
            end_time=end_date,
            limit=10000,
        )
        
        # Aggregate by billing unit
        usage_by_unit = {}
        total_cost = 0.0
        
        for event in events:
            if isinstance(event, BillingUsageEvent):
                unit = event.billing_unit
                if unit not in usage_by_unit:
                    usage_by_unit[unit] = {
                        "quantity": 0.0,
                        "total_cost": 0.0,
                        "count": 0,
                    }
                
                usage_by_unit[unit]["quantity"] += event.quantity
                usage_by_unit[unit]["total_cost"] += event.total_cost
                usage_by_unit[unit]["count"] += 1
                total_cost += event.total_cost
        
        return {
            "tenant_id": tenant_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "usage_by_unit": usage_by_unit,
            "total_cost": total_cost,
            "currency": "USD",
        }
    
    def get_billing_summary(
        self,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Get comprehensive billing summary for a tenant.
        
        Includes subscription info and usage.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Billing summary
        """
        db = next(get_db())
        
        try:
            # Get tenant
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return {"error": "Tenant not found"}
            
            # Get subscription (if exists)
            from agent_factory.database.models import Subscription, Plan
            
            subscription = db.query(Subscription).filter(
                Subscription.tenant_id == tenant_id,
                Subscription.status == "active",
            ).first()
            
            plan_info = None
            if subscription:
                plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
                if plan:
                    plan_info = {
                        "plan_id": plan.id,
                        "plan_name": plan.name,
                        "plan_type": plan.plan_type,
                        "billing_cycle": subscription.billing_cycle,
                        "current_period_start": subscription.current_period_start.isoformat(),
                        "current_period_end": subscription.current_period_end.isoformat(),
                    }
            
            # Get usage for current period
            if subscription:
                usage = self.get_usage_summary(
                    tenant_id=tenant_id,
                    start_date=subscription.current_period_start,
                    end_date=subscription.current_period_end,
                )
            else:
                usage = self.get_usage_summary(tenant_id=tenant_id)
            
            return {
                "tenant_id": tenant_id,
                "plan": plan_info or {"plan_type": tenant.plan or "free"},
                "usage": usage,
            }
        finally:
            db.close()


# Global usage tracker instance
_usage_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """
    Get global usage tracker instance.
    
    Returns:
        Usage tracker
    """
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker
