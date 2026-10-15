"""Multi-tenancy support."""

from typing import Any

from agent_factory.database.models import Tenant
from agent_factory.database.session import get_db
from agent_factory.security.audit import audit_log


def get_tenant(tenant_id: str) -> dict[str, Any] | None:
    """
    Get tenant information.
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        Tenant info or None
    """
    db = next(get_db())
    
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            return None
        
        return {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "plan": tenant.plan,
            "resource_quota": tenant.resource_quota or {},
            "usage": tenant.usage or {},
            "is_active": tenant.is_active
        }
    finally:
        db.close()


def create_tenant(
    name: str,
    slug: str,
    plan: str = "free"
) -> dict[str, Any]:
    """
    Create new tenant.
    
    Args:
        name: Tenant name
        slug: Tenant slug
        plan: Plan type (free, pro, enterprise)
        
    Returns:
        Created tenant info
    """
    db = next(get_db())
    
    try:
        # Default quotas based on plan
        quotas = {
            "free": {"agents": 5, "workflows": 3, "executions_per_month": 1000},
            "pro": {"agents": 50, "workflows": 20, "executions_per_month": 100000},
            "enterprise": {"agents": -1, "workflows": -1, "executions_per_month": -1}  # -1 = unlimited
        }
        
        tenant = Tenant(
            name=name,
            slug=slug,
            plan=plan,
            resource_quota=quotas.get(plan, quotas["free"]),
            usage={}
        )
        
        db.add(tenant)
        db.commit()
        
        audit_log(
            event_type="tenant_created",
            resource_type="tenant",
            resource_id=tenant.id,
            action="create",
            success=True
        )
        
        return {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "plan": tenant.plan
        }
    except Exception as e:
        db.rollback()
        audit_log(
            event_type="tenant_created",
            resource_type="tenant",
            action="create",
            success=False,
            details={"error": str(e)}
        )
        raise
    finally:
        db.close()


def check_quota(tenant_id: str, resource_type: str, requested_count: int = 1) -> bool:
    """
    Check if tenant has quota for resource.
    
    Args:
        tenant_id: Tenant ID
        resource_type: Resource type (agents, workflows, executions_per_month)
        requested_count: Number of resources requested
        
    Returns:
        True if quota available, False otherwise
    """
    db = next(get_db())
    
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            return False
        
        quota = tenant.resource_quota or {}
        usage = tenant.usage or {}
        
        quota_limit = quota.get(resource_type, 0)
        current_usage = usage.get(resource_type, 0)
        
        # -1 means unlimited
        if quota_limit == -1:
            return True
        
        return (current_usage + requested_count) <= quota_limit
    finally:
        db.close()


def track_usage(tenant_id: str, resource_type: str, count: int = 1):
    """
    Track resource usage for tenant.
    
    Args:
        tenant_id: Tenant ID
        resource_type: Resource type
        count: Usage count
    """
    db = next(get_db())
    
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            return
        
        usage = tenant.usage or {}
        current_usage = usage.get(resource_type, 0)
        usage[resource_type] = current_usage + count
        
        tenant.usage = usage
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
