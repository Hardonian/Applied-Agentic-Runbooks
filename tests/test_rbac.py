"""Tests for role-based access control."""

from unittest.mock import Mock

import pytest

from agent_factory.security.rbac import (
    ROLE_PERMISSIONS,
    Permission,
    Role,
    check_permission,
    get_user_permissions,
    require_permission,
    require_role,
)


@pytest.mark.unit
def test_permission_enum():
    """Test Permission enum values."""
    assert Permission.READ_AGENTS == "agents:read"
    assert Permission.WRITE_AGENTS == "agents:write"
    assert Permission.ADMIN == "admin:*"


@pytest.mark.unit
def test_role_enum():
    """Test Role enum values."""
    assert Role.USER == "user"
    assert Role.CREATOR == "creator"
    assert Role.ADMIN == "admin"


@pytest.mark.unit
def test_role_permissions_mapping():
    """Test role to permissions mapping."""
    assert Permission.READ_AGENTS in ROLE_PERMISSIONS[Role.USER]
    assert Permission.PUBLISH_BLUEPRINTS in ROLE_PERMISSIONS[Role.CREATOR]
    assert Permission.ADMIN in ROLE_PERMISSIONS[Role.ADMIN]
    assert Permission.DELETE_AGENTS in ROLE_PERMISSIONS[Role.ADMIN]


@pytest.mark.unit
def test_get_user_permissions():
    """Test getting user permissions from request."""
    request = Mock()
    request.state.user_roles = [Role.USER]
    
    permissions = get_user_permissions(request)
    
    assert Permission.READ_AGENTS in permissions
    assert Permission.WRITE_AGENTS in permissions
    assert Permission.ADMIN not in permissions


@pytest.mark.unit
def test_get_user_permissions_admin():
    """Test getting admin permissions."""
    request = Mock()
    request.state.user_roles = [Role.ADMIN]
    
    permissions = get_user_permissions(request)
    
    assert Permission.ADMIN in permissions
    assert Permission.DELETE_AGENTS in permissions


@pytest.mark.unit
def test_get_user_permissions_multiple_roles():
    """Test getting permissions for multiple roles."""
    request = Mock()
    request.state.user_roles = [Role.USER, Role.CREATOR]
    
    permissions = get_user_permissions(request)
    
    # Should have permissions from both roles
    assert Permission.READ_AGENTS in permissions
    assert Permission.PUBLISH_BLUEPRINTS in permissions


@pytest.mark.unit
def test_require_permission_decorator():
    """Test require_permission decorator structure."""
    # Test that decorator exists and can be applied
    @require_permission(Permission.READ_AGENTS)
    async def test_func(request):
        return "success"
    
    # Decorator should exist and be callable
    assert callable(test_func)


@pytest.mark.unit
def test_require_role_decorator():
    """Test require_role decorator structure."""
    # Test that decorator exists and can be applied
    @require_role(Role.ADMIN)
    async def test_func(request):
        return "success"
    
    # Decorator should exist and be callable
    assert callable(test_func)


@pytest.mark.unit
def test_explicit_permissions_are_honored_for_service_accounts():
    assert check_permission(
        {"roles": [], "permissions": [Permission.EXECUTE_WORKFLOWS.value]},
        Permission.EXECUTE_WORKFLOWS,
    )
