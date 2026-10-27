"""Role-based access control (RBAC) and enterprise permission management."""

from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request, status


class Permission(str, Enum):
    """Permission types across Agent Factory entities."""

    READ_AGENTS = "agents:read"
    WRITE_AGENTS = "agents:write"
    DELETE_AGENTS = "agents:delete"
    EXECUTE_AGENTS = "agents:execute"
    READ_WORKFLOWS = "workflows:read"
    WRITE_WORKFLOWS = "workflows:write"
    DELETE_WORKFLOWS = "workflows:delete"
    EXECUTE_WORKFLOWS = "workflows:execute"
    READ_BLUEPRINTS = "blueprints:read"
    PUBLISH_BLUEPRINTS = "blueprints:publish"
    DELETE_BLUEPRINTS = "blueprints:delete"
    READ_ANALYTICS = "analytics:read"
    MANAGE_BILLING = "billing:manage"
    ADMIN = "admin:*"


class Role(str, Enum):
    """System and workspace role levels."""

    VIEWER = "viewer"
    USER = "user"
    CREATOR = "creator"
    ADMIN = "admin"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.VIEWER: [
        Permission.READ_AGENTS,
        Permission.READ_WORKFLOWS,
        Permission.READ_BLUEPRINTS,
        Permission.READ_ANALYTICS,
    ],
    Role.USER: [
        Permission.READ_AGENTS,
        Permission.WRITE_AGENTS,
        Permission.EXECUTE_AGENTS,
        Permission.READ_WORKFLOWS,
        Permission.WRITE_WORKFLOWS,
        Permission.EXECUTE_WORKFLOWS,
        Permission.READ_BLUEPRINTS,
        Permission.READ_ANALYTICS,
    ],
    Role.CREATOR: [
        Permission.READ_AGENTS,
        Permission.WRITE_AGENTS,
        Permission.EXECUTE_AGENTS,
        Permission.READ_WORKFLOWS,
        Permission.WRITE_WORKFLOWS,
        Permission.EXECUTE_WORKFLOWS,
        Permission.READ_BLUEPRINTS,
        Permission.PUBLISH_BLUEPRINTS,
        Permission.READ_ANALYTICS,
    ],
    Role.ADMIN: [
        Permission.READ_AGENTS,
        Permission.WRITE_AGENTS,
        Permission.DELETE_AGENTS,
        Permission.EXECUTE_AGENTS,
        Permission.READ_WORKFLOWS,
        Permission.WRITE_WORKFLOWS,
        Permission.DELETE_WORKFLOWS,
        Permission.EXECUTE_WORKFLOWS,
        Permission.READ_BLUEPRINTS,
        Permission.PUBLISH_BLUEPRINTS,
        Permission.DELETE_BLUEPRINTS,
        Permission.READ_ANALYTICS,
        Permission.MANAGE_BILLING,
        Permission.ADMIN,
    ],
}


def get_user_permissions(request: Request) -> list[Permission]:
    """
    Get user permissions from request state.

    Args:
        request: FastAPI request

    Returns:
        List of granted permissions
    """
    user_roles = getattr(request.state, "user_roles", [Role.USER])
    permissions = []

    for role in user_roles:
        if isinstance(role, str):
            try:
                role = Role(role)
            except ValueError:
                continue
        if role in ROLE_PERMISSIONS:
            permissions.extend(ROLE_PERMISSIONS[role])

    return list(set(permissions))


def check_permission(
    user: dict[str, Any] | Any, permission: Permission | str, resource_id: str | None = None
) -> bool:
    """
    Check if user has a specific permission.

    Args:
        user: User dict or user model object
        permission: Permission enum or string
        resource_id: Optional target resource ID

    Returns:
        True if user has permission or is admin, else False
    """
    if isinstance(user, dict):
        user_roles = user.get("roles", [Role.USER])
        explicit_permissions = user.get("permissions", [])
    else:
        user_roles = getattr(user, "roles", [Role.USER])
        explicit_permissions = getattr(user, "permissions", [])

    user_perms: list[Permission] = []
    for role in user_roles:
        if isinstance(role, str):
            try:
                role = Role(role)
            except ValueError:
                continue
        if role in ROLE_PERMISSIONS:
            user_perms.extend(ROLE_PERMISSIONS[role])

    # API keys and service accounts can carry scoped permissions independent
    # of a broad interactive role.  Treat valid explicit permissions as
    # additive; silently ignore malformed values rather than granting access.
    for explicit_permission in explicit_permissions:
        try:
            user_perms.append(Permission(explicit_permission))
        except ValueError:
            continue

    if Permission.ADMIN in user_perms:
        return True

    target_perm = Permission(permission) if isinstance(permission, str) else permission
    return target_perm in user_perms


def require_user_permission(user: dict[str, Any] | Any, permission: Permission) -> None:
    """Raise a 403 unless an authenticated user holds ``permission``.

    Route handlers use this helper after resolving the authenticated user. The
    decorator below is retained for handlers that receive a ``Request``;
    invoking that decorator manually does not enforce anything.
    """
    if not check_permission(user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission required: {permission.value}",
        )


def require_permission(permission: Permission):
    """
    Decorator for FastAPI endpoint handlers to enforce required permissions.
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None and "request" in kwargs:
                request = kwargs["request"]

            if request:
                perms = get_user_permissions(request)
                if Permission.ADMIN not in perms and permission not in perms:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission required: {permission.value}",
                    )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: Role):
    """
    Decorator for FastAPI endpoint handlers to enforce required role level.
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None and "request" in kwargs:
                request = kwargs["request"]

            if request:
                user_roles = getattr(request.state, "user_roles", [])
                if Role.ADMIN not in user_roles and role not in user_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail=f"Role required: {role.value}"
                    )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
