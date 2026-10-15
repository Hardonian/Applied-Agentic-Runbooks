"""Database models."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from agent_factory.database.session import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    roles = Column(JSON, default=list)
    permissions = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    plan = Column(String, default="free")  # free, pro, enterprise
    resource_quota = Column(JSON, default=dict)  # {"agents": 10, "workflows": 5}
    usage = Column(JSON, default=dict)  # {"agents": 0, "workflows": 0}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    instructions = Column(Text, nullable=False)
    model = Column(String, default="gpt-4o")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant: Any = relationship("Tenant")
    creator: Any = relationship("User")

    def __init__(self, **kwargs):
        kwargs.setdefault("model", "gpt-4o")
        super().__init__(**kwargs)


class Workflow(Base):
    """Workflow model."""
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    definition = Column(JSON, nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant: Any = relationship("Tenant")
    creator: Any = relationship("User")


class Blueprint(Base):
    """Blueprint model."""
    __tablename__ = "blueprints"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    version = Column(String, nullable=False)
    definition = Column(JSON, nullable=False)
    pricing_model = Column(String, default="free")  # free, one-time, subscription
    price = Column(Float, default=0.0)
    publisher_id = Column(String, ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=False)
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    
    id = Column(String, primary_key=True)
    execution_type = Column(String, nullable=False)  # agent, workflow
    resource_id = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending, running, completed, failed
    input_data = Column(JSON)
    output_data = Column(JSON)
    error = Column(Text)
    execution_time = Column(Float)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    tenant: Any = relationship("Tenant")
    creator: Any = relationship("User")


class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    resource_type = Column(String)
    resource_id = Column(String)
    action = Column(String)
    success = Column(Boolean, default=True)
    details = Column(JSON)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user: Any = relationship("User")


class APIKey(Base):
    """API key model for programmatic access."""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True)
    key_hash = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    permissions = Column(JSON, default=list)
    last_used_at: Any = Column(DateTime, nullable=True)
    expires_at: Any = Column(DateTime, nullable=True)
    is_active: Any = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant: Any = relationship("Tenant")
    user: Any = relationship("User")


class Project(Base):
    """Project/App model for organizing resources."""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    project_type = Column(String, default="saas_app")  # saas_app, blueprint_deployment, etc.
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant: Any = relationship("Tenant")
    creator: Any = relationship("User")


class Plan(Base):
    """Billing plan model."""
    __tablename__ = "plans"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    plan_type = Column(String, nullable=False)  # free, pro, enterprise
    price_monthly: Any = Column(Float, default=0.0)
    price_yearly: Any = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    features = Column(JSON, default=dict)
    limits = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Subscription(Base):
    """Subscription model."""
    __tablename__ = "subscriptions"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False)
    status = Column(String, default="active")  # active, cancelled, expired
    billing_cycle = Column(String, default="monthly")  # monthly, yearly
    current_period_start: Any = Column(DateTime, nullable=False)
    current_period_end: Any = Column(DateTime, nullable=False)
    stripe_subscription_id = Column(String, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant: Any = relationship("Tenant")
    plan: Any = relationship("Plan")


class UsageRecord(Base):
    """Usage record for billing."""
    __tablename__ = "usage_records"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    subscription_id = Column(String, ForeignKey("subscriptions.id"), nullable=True)
    billing_unit = Column(String, nullable=False)  # agent_run, workflow_run, token, etc.
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant: Any = relationship("Tenant")
    subscription: Any = relationship("Subscription")


class ArenaRun(Base):
    """Durable, tenant-scoped autonomous Arena execution record."""

    __tablename__ = "arena_runs"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True, default="public")
    created_by = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, index=True, default="queued")
    mode = Column(String, nullable=False, default="deterministic")
    benchmark_version = Column(String, nullable=False, default="2026.10")
    request = Column(JSON, nullable=False, default=dict)
    summary = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    cancel_requested = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)


class ApprovalTicket(Base):
    """Authoritative MCPWall ticket and immutable operator decision receipt."""

    __tablename__ = "approval_tickets"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True, default="public")
    tool_name = Column(String, nullable=False)
    request_hash = Column(String, nullable=False, index=True)
    arguments = Column(JSON, nullable=False, default=dict)
    requested_by = Column(String, nullable=True)
    status = Column(String, nullable=False, index=True, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String, nullable=True)
    decision_reason = Column(Text, nullable=True)
    receipt_signature = Column(String, nullable=True)
    consumed_at = Column(DateTime, nullable=True)
