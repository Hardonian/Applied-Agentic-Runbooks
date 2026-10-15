"""
Cost tracking and financial management for Agent Factory Platform.

Tracks costs per agent, workflow, user, and tenant with budget management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any


class CostType(str, Enum):
    """Types of costs."""
    LLM_API = "llm_api"
    STORAGE = "storage"
    COMPUTE = "compute"
    BANDWIDTH = "bandwidth"
    TOOL_USAGE = "tool_usage"


@dataclass
class CostRecord:
    """Record of a cost event."""
    id: str
    timestamp: datetime
    cost_type: CostType
    amount: Decimal
    entity_type: str  # "agent", "workflow", "user", "tenant"
    entity_id: str
    currency: str = "USD"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Budget:
    """Budget definition."""
    id: str
    name: str
    entity_type: str
    entity_id: str
    amount: Decimal
    currency: str = "USD"
    period: str = "monthly"  # "daily", "weekly", "monthly", "yearly"
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: datetime | None = None
    alert_threshold: Decimal = Decimal("0.8")  # Alert at 80%


class CostTracker:
    """
    Tracks costs and manages budgets.
    
    Example:
        >>> tracker = CostTracker()
        >>> tracker.record_cost(
        ...     cost_type=CostType.LLM_API,
        ...     amount=Decimal("0.05"),
        ...     entity_type="agent",
        ...     entity_id="my-agent"
        ... )
        >>> total = tracker.get_total_cost("agent", "my-agent")
    """
    
    def __init__(self):
        """Initialize cost tracker."""
        self.costs: list[CostRecord] = []
        self.budgets: dict[str, Budget] = {}
        self._cost_cache: dict[str, Decimal] = {}
    
    def record_cost(
        self,
        cost_type: CostType,
        amount: Decimal,
        entity_type: str,
        entity_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Record a cost event.
        
        Args:
            cost_type: Type of cost
            amount: Cost amount
            entity_type: Entity type (agent, workflow, user, tenant)
            entity_id: Entity identifier
            metadata: Optional metadata
            
        Returns:
            Cost record ID
        """
        import uuid
        record_id = str(uuid.uuid4())
        
        record = CostRecord(
            id=record_id,
            timestamp=datetime.utcnow(),
            cost_type=cost_type,
            amount=amount,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
        )
        
        self.costs.append(record)
        
        # Update cache
        cache_key = f"{entity_type}:{entity_id}"
        self._cost_cache[cache_key] = self._cost_cache.get(cache_key, Decimal(0)) + amount
        
        # Check budgets
        self._check_budgets(entity_type, entity_id, amount)
        
        return record_id
    
    def get_total_cost(
        self,
        entity_type: str,
        entity_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Decimal:
        """
        Get total cost for an entity.
        
        Args:
            entity_type: Entity type
            entity_id: Entity identifier
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            
        Returns:
            Total cost
        """
        cache_key = f"{entity_type}:{entity_id}"
        
        # If no date filter, use cache
        if start_date is None and end_date is None:
            return self._cost_cache.get(cache_key, Decimal(0))
        
        # Calculate with date filter
        total = Decimal(0)
        for cost in self.costs:
            if cost.entity_type == entity_type and cost.entity_id == entity_id:
                if start_date and cost.timestamp < start_date:
                    continue
                if end_date and cost.timestamp > end_date:
                    continue
                total += cost.amount
        
        return total
    
    def get_costs_by_type(
        self,
        cost_type: CostType,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[CostRecord]:
        """
        Get costs by type.
        
        Args:
            cost_type: Cost type
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of cost records
        """
        results = [c for c in self.costs if c.cost_type == cost_type]
        
        if start_date:
            results = [c for c in results if c.timestamp >= start_date]
        if end_date:
            results = [c for c in results if c.timestamp <= end_date]
        
        return results
    
    def create_budget(
        self,
        name: str,
        entity_type: str,
        entity_id: str,
        amount: Decimal,
        period: str = "monthly",
        alert_threshold: Decimal = Decimal("0.8"),
    ) -> str:
        """
        Create a budget.
        
        Args:
            name: Budget name
            entity_type: Entity type
            entity_id: Entity identifier
            amount: Budget amount
            period: Budget period
            alert_threshold: Alert threshold (0-1)
            
        Returns:
            Budget ID
        """
        import uuid
        budget_id = str(uuid.uuid4())
        
        budget = Budget(
            id=budget_id,
            name=name,
            entity_type=entity_type,
            entity_id=entity_id,
            amount=amount,
            period=period,
            alert_threshold=alert_threshold,
        )
        
        self.budgets[budget_id] = budget
        return budget_id
    
    def get_budget_status(self, budget_id: str) -> dict[str, Any]:
        """
        Get budget status.
        
        Args:
            budget_id: Budget ID
            
        Returns:
            Budget status dictionary
        """
        budget = self.budgets.get(budget_id)
        if not budget:
            raise ValueError(f"Budget not found: {budget_id}")
        
        # Calculate period start/end
        now = datetime.utcnow()
        period_start, period_end = self._get_period_dates(budget.period, now)
        
        # Get costs for period
        total_cost = self.get_total_cost(
            budget.entity_type,
            budget.entity_id,
            start_date=period_start,
            end_date=period_end,
        )
        
        usage_percent = float(total_cost / budget.amount) if budget.amount > 0 else 0.0
        remaining = budget.amount - total_cost
        is_over_budget = total_cost > budget.amount
        should_alert = usage_percent >= float(budget.alert_threshold)
        
        return {
            "budget_id": budget_id,
            "budget_name": budget.name,
            "budget_amount": float(budget.amount),
            "total_cost": float(total_cost),
            "remaining": float(remaining),
            "usage_percent": usage_percent * 100,
            "is_over_budget": is_over_budget,
            "should_alert": should_alert,
            "period": budget.period,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }
    
    def _get_period_dates(self, period: str, reference_date: datetime) -> tuple:
        """Get period start and end dates."""
        if period == "daily":
            start = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == "weekly":
            days_since_monday = reference_date.weekday()
            start = reference_date - timedelta(days=days_since_monday)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(weeks=1)
        elif period == "monthly":
            start = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        elif period == "yearly":
            start = reference_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
        else:
            raise ValueError(f"Unknown period: {period}")
        
        return start, end
    
    def _check_budgets(self, entity_type: str, entity_id: str, amount: Decimal) -> None:
        """Check budgets and trigger alerts if needed."""
        for budget in self.budgets.values():
            if budget.entity_type == entity_type and budget.entity_id == entity_id:
                status = self.get_budget_status(budget.id)
                if status["should_alert"] or status["is_over_budget"]:
                    # Trigger alert (would integrate with alerting system)
                    self._trigger_budget_alert(budget, status)
    
    def _trigger_budget_alert(self, budget: Budget, status: dict[str, Any]) -> None:
        """Trigger budget alert."""
        # Would integrate with alerting system
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Budget alert: {budget.name}",
            extra={
                "budget_id": budget.id,
                "usage_percent": status["usage_percent"],
                "is_over_budget": status["is_over_budget"],
            }
        )
    
    def get_cost_breakdown(
        self,
        entity_type: str,
        entity_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Decimal]:
        """
        Get cost breakdown by type.
        
        Args:
            entity_type: Entity type
            entity_id: Entity identifier
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Dictionary of cost type to amount
        """
        breakdown = {cost_type.value: Decimal(0) for cost_type in CostType}
        
        for cost in self.costs:
            if cost.entity_type == entity_type and cost.entity_id == entity_id:
                if start_date and cost.timestamp < start_date:
                    continue
                if end_date and cost.timestamp > end_date:
                    continue
                breakdown[cost.cost_type.value] += cost.amount
        
        return breakdown
    
    def estimate_cost(
        self,
        entity_type: str,
        entity_id: str,
        tokens: int,
        model: str = "gpt-4o",
    ) -> Decimal:
        """
        Estimate cost based on tokens and model.
        
        Args:
            entity_type: Entity type
            entity_id: Entity identifier
            tokens: Number of tokens
            model: Model name
            
        Returns:
            Estimated cost
        """
        # Model pricing (per 1K tokens)
        pricing = {
            "gpt-4o": {"input": Decimal("0.0025"), "output": Decimal("0.01")},
            "gpt-4": {"input": Decimal("0.03"), "output": Decimal("0.06")},
            "gpt-3.5-turbo": {"input": Decimal("0.0005"), "output": Decimal("0.0015")},
            "claude-3-opus": {"input": Decimal("0.015"), "output": Decimal("0.075")},
            "claude-3-sonnet": {"input": Decimal("0.003"), "output": Decimal("0.015")},
        }
        
        model_pricing = pricing.get(model, pricing["gpt-4o"])
        
        # Estimate 70% input, 30% output
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)
        
        input_cost = (Decimal(input_tokens) / 1000) * model_pricing["input"]
        output_cost = (Decimal(output_tokens) / 1000) * model_pricing["output"]
        
        total_cost = input_cost + output_cost
        
        # Record estimated cost
        self.record_cost(
            cost_type=CostType.LLM_API,
            amount=total_cost,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata={"tokens": tokens, "model": model, "estimated": True},
        )
        
        return total_cost


# Global instance
_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
