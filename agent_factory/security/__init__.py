"""Security and authentication module."""

from agent_factory.security.audit import AuditLogger, audit_log
from agent_factory.security.auth import (
    JWTBearer,
    create_access_token,
    get_current_user,
    verify_token,
)
from agent_factory.security.mcpwall import (
    HumanApprovalTicket,
    MCPWall,
    MCPWallSecurityError,
    MCPWallVerdict,
)
from agent_factory.security.rate_limit import RateLimitMiddleware, setup_rate_limiting
from agent_factory.security.rbac import (
    Permission,
    Role,
    require_permission,
    require_role,
)
from agent_factory.security.sanitization import sanitize_input, sanitize_output

__all__ = [
    "AuditLogger",
    "HumanApprovalTicket",
    "JWTBearer",
    "MCPWall",
    "MCPWallSecurityError",
    "MCPWallVerdict",
    "Permission",
    "RateLimitMiddleware",
    "Role",
    "audit_log",
    "create_access_token",
    "get_current_user",
    "require_permission",
    "require_role",
    "sanitize_input",
    "sanitize_output",
    "setup_rate_limiting",
    "verify_token",
]
