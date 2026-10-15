"""
Billing data models.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Plan:
    """Billing plan."""
    id: str
    name: str
    plan_type: str = "free"  # free, pro, enterprise
    # ``price`` remains a convenience alias for one-time/simple plan callers;
    # recurring plans should use the explicit monthly/yearly fields.
    price: float | None = None
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    currency: str = "USD"
    features: dict[str, Any] | None = None
    limits: dict[str, Any] | None = None
    
    def __post_init__(self):
        if self.price is not None and self.price_monthly == 0.0:
            self.price_monthly = self.price
        if self.price is None:
            self.price = self.price_monthly
        if self.features is None:
            self.features = {}
        if self.limits is None:
            self.limits = {}


@dataclass
class Subscription:
    """Subscription to a plan."""
    id: str
    tenant_id: str
    plan_id: str
    status: str = "active"  # active, cancelled, expired
    billing_cycle: str = "monthly"  # monthly, yearly
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    stripe_subscription_id: str | None = None
    stripe_customer_id: str | None = None
    
    def __post_init__(self):
        if self.current_period_start is None:
            self.current_period_start = datetime.utcnow()
        if self.current_period_end is None:
            self.current_period_end = datetime.utcnow()


@dataclass
class UsageRecord:
    """Usage record for billing."""
    id: str
    tenant_id: str
    billing_unit: str  # agent_run, workflow_run, token, etc.
    quantity: float
    unit_price: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"
    period_start: datetime | None = None
    period_end: datetime | None = None
    
    def __post_init__(self):
        if self.period_start is None:
            self.period_start = datetime.utcnow()
        if self.period_end is None:
            self.period_end = datetime.utcnow()
        if self.total_cost == 0.0 and self.quantity > 0:
            self.total_cost = self.quantity * self.unit_price
