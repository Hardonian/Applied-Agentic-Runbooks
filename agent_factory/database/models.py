"""Database models."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agent_factory.database.session import Base


class User(Base):
    """User model."""

    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    tenant_id: Mapped[str | None] = mapped_column(String, ForeignKey("tenants.id"), nullable=True)
    roles: Mapped[Any] = mapped_column(JSON, default=list)
    permissions: Mapped[Any] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant: Any = relationship("Tenant", back_populates="users")

    def __init__(self, **kwargs):
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_superuser", False)
        kwargs.setdefault("roles", [])
        kwargs.setdefault("permissions", [])
        super().__init__(**kwargs)


class Tenant(Base):
    """Tenant model for multi-tenancy."""

    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    plan: Mapped[str] = mapped_column(String, default="free")  # free, pro, enterprise
    resource_quota: Mapped[Any] = mapped_column(JSON, default=dict)  # {"agents": 10, ...}
    usage: Mapped[Any] = mapped_column(JSON, default=dict)  # {"agents": 0, ...}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    users: Any = relationship("User", back_populates="tenant")

    def __init__(self, **kwargs):
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("plan", "free")
        kwargs.setdefault("resource_quota", {})
        kwargs.setdefault("usage", {})
        super().__init__(**kwargs)


class Agent(Base):
    """Agent model."""

    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String, default="gpt-4o")
    tenant_id: Mapped[str | None] = mapped_column(String, ForeignKey("tenants.id"), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant: Any = relationship("Tenant")
    creator: Any = relationship("User")

    def __init__(self, **kwargs):
        kwargs.setdefault("model", "gpt-4o")
        super().__init__(**kwargs)


class Workflow(Base):
    """Workflow model."""

    __tablename__ = "workflows"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    definition: Mapped[Any] = mapped_column(JSON, nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String, ForeignKey("tenants.id"), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant: Any = relationship("Tenant")
    creator: Any = relationship("User")


class Blueprint(Base):
    """Blueprint model."""

    __tablename__ = "blueprints"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    definition: Mapped[Any] = mapped_column(JSON, nullable=False)
    pricing_model: Mapped[str] = mapped_column(String, default="free")  # free, one-time, sub
    price: Mapped[float] = mapped_column(Float, default=0.0)
    publisher_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    publisher: Any = relationship("User")

    def __init__(self, **kwargs):
        kwargs.setdefault("pricing_model", "free")
        kwargs.setdefault("price", 0.0)
        kwargs.setdefault("is_public", False)
        kwargs.setdefault("downloads", 0)
        kwargs.setdefault("rating", 0.0)
        kwargs.setdefault("reviews_count", 0)
        super().__init__(**kwargs)


class Execution(Base):
    """Execution model."""

    __tablename__ = "executions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    execution_type: Mapped[str] = mapped_column(String, nullable=False)  # agent, workflow
    resource_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # pending, running, completed
    input_data: Mapped[Any] = mapped_column(JSON)
    output_data: Mapped[Any] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String, ForeignKey("tenants.id"), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tenant: Any = relationship("Tenant")
    creator: Any = relationship("User")


class AuditLog(Base):
    """Audit log model."""

    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String, nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str | None] = mapped_column(String, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    details: Mapped[Any] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user: Any = relationship("User")


class APIKey(Base):
    """API key model for programmatic access."""

    __tablename__ = "api_keys"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    key_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    permissions: Mapped[Any] = mapped_column(JSON, default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant: Any = relationship("Tenant")
    user: Any = relationship("User")


class Project(Base):
    """Project/App model for organizing resources."""

    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    project_type: Mapped[str] = mapped_column(String, default="saas_app")  # saas_app, blueprint
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    config: Mapped[Any] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant: Any = relationship("Tenant")
    creator: Any = relationship("User")


class Plan(Base):
    """Billing plan model."""

    __tablename__ = "plans"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    plan_type: Mapped[str] = mapped_column(String, nullable=False)  # free, pro, enterprise
    price_monthly: Mapped[float] = mapped_column(Float, default=0.0)
    price_yearly: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String, default="USD")
    features: Mapped[Any] = mapped_column(JSON, default=dict)
    limits: Mapped[Any] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Subscription(Base):
    """Subscription model."""

    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("plans.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")  # active, cancelled, expired
    billing_cycle: Mapped[str] = mapped_column(String, default="monthly")  # monthly, yearly
    current_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant: Any = relationship("Tenant")
    plan: Any = relationship("Plan")

    def __init__(self, **kwargs):
        kwargs.setdefault("id", str(uuid.uuid4()))
        now = datetime.utcnow()
        kwargs.setdefault("status", "active")
        kwargs.setdefault("billing_cycle", "monthly")
        kwargs.setdefault("current_period_start", now)
        kwargs.setdefault("current_period_end", now + timedelta(days=30))
        super().__init__(**kwargs)


class UsageRecord(Base):
    """Usage record for billing."""

    __tablename__ = "usage_records"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), nullable=False)
    subscription_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("subscriptions.id"), nullable=True
    )
    billing_unit: Mapped[str] = mapped_column(String, nullable=False)  # agent_run, workflow_run
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String, default="USD")
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tenant: Any = relationship("Tenant")
    subscription: Any = relationship("Subscription")


class ArenaRun(Base):
    """Durable, tenant-scoped autonomous Arena execution record."""

    __tablename__ = "arena_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True, default="public")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True, default="queued")
    mode: Mapped[str] = mapped_column(String, nullable=False, default="deterministic")
    benchmark_version: Mapped[str] = mapped_column(String, nullable=False, default="2026.10")
    request: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    summary: Mapped[Any] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class ApprovalTicket(Base):
    """Authoritative MCPWall ticket and immutable operator decision receipt."""

    __tablename__ = "approval_tickets"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True, default="public")
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    request_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    arguments: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    requested_by: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_signature: Mapped[str | None] = mapped_column(String, nullable=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
