"""Security and authentication module."""

from agent_factory.security.audit import AuditLogger, audit_log
from agent_factory.security.auth import (
    JWTBearer,
    create_access_token,
    get_current_user,
    verify_token,
)
from agent_factory.security.rate_limit import RateLimitMiddleware, setup_rate_limiting
from agent_factory.security.rbac import Permission, Role, require_permission, require_role
from agent_factory.security.sanitization import sanitize_input, sanitize_output

__all__ = [
    "JWTBearer",
    "get_current_user",
    "create_access_token",
    "verify_token",
    "require_permission",
    "require_role",
    "Permission",
    "Role",
    "RateLimitMiddleware",
    "setup_rate_limiting",
    "sanitize_input",
    "sanitize_output",
    "AuditLogger",
    "audit_log",
]
