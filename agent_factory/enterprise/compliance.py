"""Compliance features (SOC2, GDPR)."""

from datetime import datetime, timedelta
from typing import Any

from agent_factory.database.models import AuditLog as AuditLogModel
from agent_factory.database.models import Execution, User
from agent_factory.database.session import get_db
from agent_factory.security.audit import audit_log


def enable_audit_trail(tenant_id: str) -> dict[str, Any]:
    """
    Enable audit trail for tenant.

    Args:
        tenant_id: Tenant ID

    Returns:
        Audit trail configuration
    """
    # Audit trail is always enabled, this is for configuration
    return {"tenant_id": tenant_id, "audit_trail_enabled": True, "retention_days": 90}


def enforce_data_retention(tenant_id: str, retention_days: int = 90):
    """
    Enforce data retention policy.

    Args:
        tenant_id: Tenant ID
        retention_days: Retention period in days
    """
    db = next(get_db())

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Delete old audit logs
        deleted_logs = (
            db.query(AuditLogModel).filter(AuditLogModel.created_at < cutoff_date).delete()
        )

        # Delete old executions
        deleted_executions = (
            db.query(Execution)
            .filter(Execution.created_at < cutoff_date, Execution.tenant_id == tenant_id)
            .delete()
        )

        db.commit()

        audit_log(
            event_type="data_retention_enforced",
            resource_type="tenant",
            resource_id=tenant_id,
            action="delete",
            success=True,
            details={
                "retention_days": retention_days,
                "deleted_logs": deleted_logs,
                "deleted_executions": deleted_executions,
            },
        )

        return {
            "tenant_id": tenant_id,
            "deleted_logs": deleted_logs,
            "deleted_executions": deleted_executions,
        }
    except Exception as e:
        db.rollback()
        audit_log(
            event_type="data_retention_enforced",
            resource_type="tenant",
            resource_id=tenant_id,
            action="delete",
            success=False,
            details={"error": str(e)},
        )
        raise
    finally:
        db.close()


def export_user_data(user_id: str) -> dict[str, Any]:
    """
    Export user data for GDPR compliance.

    Args:
        user_id: User ID

    Returns:
        User data export
    """
    db = next(get_db())

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {}

        # Get user's executions
        executions = db.query(Execution).filter(Execution.created_by == user_id).all()

        # Get audit logs for user
        audit_logs = db.query(AuditLogModel).filter(AuditLogModel.user_id == user_id).all()

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
            "executions": [
                {
                    "id": ex.id,
                    "type": ex.execution_type,
                    "resource_id": ex.resource_id,
                    "status": ex.status,
                    "created_at": ex.created_at.isoformat() if ex.created_at else None,
                }
                for ex in executions
            ],
            "audit_logs": [
                {
                    "event_type": log.event_type,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "action": log.action,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in audit_logs
            ],
            "exported_at": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()


def delete_user_data(user_id: str) -> dict[str, Any]:
    """
    Delete user data for GDPR right to be forgotten.

    Args:
        user_id: User ID

    Returns:
        Deletion result
    """
    db = next(get_db())

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"status": "user_not_found"}

        # Anonymize user data instead of deleting (for audit trail)
        user.email = f"deleted_{user_id}@deleted.local"
        user.is_active = False

        # Delete user's executions
        deleted_executions = db.query(Execution).filter(Execution.created_by == user_id).delete()

        db.commit()

        audit_log(
            event_type="user_data_deleted",
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            action="delete",
            success=True,
            details={"deleted_executions": deleted_executions},
        )

        return {"user_id": user_id, "status": "deleted", "deleted_executions": deleted_executions}
    except Exception as e:
        db.rollback()
        audit_log(
            event_type="user_data_deleted",
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            action="delete",
            success=False,
            details={"error": str(e)},
        )
        raise
    finally:
        db.close()
