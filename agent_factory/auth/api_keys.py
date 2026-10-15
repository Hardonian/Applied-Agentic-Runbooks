"""
API key management for programmatic access.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any

from agent_factory.database.models import APIKey
from agent_factory.database.session import get_db
from agent_factory.security.audit import audit_log


def generate_api_key() -> str:
    """
    Generate a new API key.
    
    Returns:
        API key string (format: af_...)
    """
    # Generate 32 bytes of random data
    secrets.token_bytes(32)
    # Encode as base64-like string, prefixed with af_
    key = "af_" + secrets.token_urlsafe(32)
    return key


def hash_api_key(key: str) -> str:
    """
    Hash an API key for storage.
    
    Args:
        key: API key string
        
    Returns:
        Hashed key
    """
    return hashlib.sha256(key.encode()).hexdigest()


def create_api_key(
    name: str,
    tenant_id: str,
    user_id: str,
    permissions: list | None = None,
    expires_days: int | None = None,
) -> dict[str, Any]:
    """
    Create a new API key.
    
    Args:
        name: API key name/description
        tenant_id: Tenant ID
        user_id: User ID creating the key
        permissions: Optional list of permissions
        expires_days: Optional expiration in days
        
    Returns:
        Dictionary with api_key and key_id
    """
    db = next(get_db())
    
    try:
        # Generate key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        # Check if hash already exists (extremely unlikely but check anyway)
        existing = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
        if existing:
            # Regenerate if collision
            api_key = generate_api_key()
            key_hash = hash_api_key(api_key)
        
        # Create key ID
        key_id = f"key_{secrets.token_urlsafe(16)}"
        
        # Set expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        # Create API key record
        api_key_model = APIKey(
            id=key_id,
            key_hash=key_hash,
            name=name,
            tenant_id=tenant_id,
            user_id=user_id,
            permissions=permissions or [],
            expires_at=expires_at,
            is_active=True,
        )
        
        db.add(api_key_model)
        db.commit()
        
        audit_log(
            event_type="api_key_created",
            user_id=user_id,
            resource_type="api_key",
            resource_id=key_id,
            action="create",
            success=True,
        )
        
        return {
            "key_id": key_id,
            "api_key": api_key,  # Only returned once!
            "name": name,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
    except Exception as e:
        db.rollback()
        audit_log(
            event_type="api_key_created",
            user_id=user_id,
            resource_type="api_key",
            action="create",
            success=False,
            details={"error": str(e)},
        )
        raise
    finally:
        db.close()


def verify_api_key(api_key: str) -> dict[str, Any] | None:
    """
    Verify an API key and return associated user/tenant info.
    
    Args:
        api_key: API key string
        
    Returns:
        Dictionary with user_id, tenant_id, permissions, or None if invalid
    """
    db = next(get_db())
    
    try:
        key_hash = hash_api_key(api_key)
        
        # Find API key
        api_key_model = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
        ).first()
        
        if not api_key_model:
            return None
        
        # Check expiration
        if api_key_model.expires_at and api_key_model.expires_at < datetime.utcnow():
            return None
        
        # Update last used
        api_key_model.last_used_at = datetime.utcnow()
        db.commit()
        
        return {
            "key_id": api_key_model.id,
            "user_id": api_key_model.user_id,
            "tenant_id": api_key_model.tenant_id,
            "permissions": api_key_model.permissions or [],
        }
    finally:
        db.close()


def revoke_api_key(key_id: str, user_id: str) -> bool:
    """
    Revoke an API key.
    
    Args:
        key_id: API key ID
        user_id: User ID (for authorization check)
        
    Returns:
        True if revoked, False if not found
    """
    db = next(get_db())
    
    try:
        api_key_model = db.query(APIKey).filter(APIKey.id == key_id).first()
        
        if not api_key_model:
            return False
        
        # Check authorization (user must own key or be tenant admin)
        if api_key_model.user_id != user_id:
            # Check if user is tenant admin
            from agent_factory.database.models import Tenant, User
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                tenant = db.query(Tenant).filter(Tenant.id == api_key_model.tenant_id).first()
                if tenant and tenant.admin_user_id == user_id:
                    # User is tenant admin, allow
                    pass
                else:
                    return False
            else:
                return False
        
        api_key_model.is_active = False
        db.commit()
        
        audit_log(
            event_type="api_key_revoked",
            user_id=user_id,
            resource_type="api_key",
            resource_id=key_id,
            action="revoke",
            success=True,
        )
        
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


def list_api_keys(tenant_id: str, user_id: str | None = None) -> list:
    """
    List API keys for a tenant.
    
    Args:
        tenant_id: Tenant ID
        user_id: Optional user ID filter
        
    Returns:
        List of API key info (without actual keys)
    """
    db = next(get_db())
    
    try:
        query = db.query(APIKey).filter(
            APIKey.tenant_id == tenant_id,
            APIKey.is_active == True,
        )
        
        if user_id:
            query = query.filter(APIKey.user_id == user_id)
        
        keys = query.all()
        
        return [
            {
                "key_id": k.id,
                "name": k.name,
                "permissions": k.permissions,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "created_at": k.created_at.isoformat(),
            }
            for k in keys
        ]
    finally:
        db.close()
