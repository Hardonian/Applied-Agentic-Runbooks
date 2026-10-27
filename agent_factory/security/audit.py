"""Audit logging."""

from datetime import datetime
from typing import Any

from agent_factory.monitoring.logging import StructuredLogger


class AuditLogger:
    """Audit logger for security events."""

    def __init__(self):
        """Initialize audit logger."""
        self.logger = StructuredLogger("audit", level="INFO")

    def log_event(
        self,
        event_type: str,
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        success: bool = True,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ):
        """
        Log audit event.

        Args:
            event_type: Type of event (auth, access, modification, etc.)
            user_id: User ID
            resource_type: Type of resource (agent, workflow, blueprint)
            resource_id: Resource ID
            action: Action performed (create, read, update, delete)
            success: Whether action was successful
            details: Additional details
            ip_address: IP address of requester
        """
        log_data = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "success": success,
            "ip_address": ip_address,
            **(details or {}),
        }

        self.logger.info(f"Audit event: {event_type}", **log_data)


# Global audit logger instance
_audit_logger = AuditLogger()


def audit_log(
    event_type: str,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    action: str | None = None,
    success: bool = True,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
):
    """
    Log audit event (convenience function).

    Args:
        event_type: Type of event
        user_id: User ID
        resource_type: Type of resource
        resource_id: Resource ID
        action: Action performed
        success: Whether action was successful
        details: Additional details
        ip_address: IP address of requester
    """
    _audit_logger.log_event(
        event_type=event_type,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        success=success,
        details=details,
        ip_address=ip_address,
    )
