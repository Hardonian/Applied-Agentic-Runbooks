"""JWT authentication."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    """User model."""
    id: str
    email: str
    roles: list[str] = []
    permissions: list[str] = []
    tenant_id: str | None = None


class TokenData(BaseModel):
    """Token data model."""
    user_id: str | None = None
    email: str | None = None


security = HTTPBearer()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Optional expiration delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Token data
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenData(user_id=str(user_id), email=str(email or ""))
        return token_data
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication."""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request, credentials: HTTPAuthorizationCredentials = Security(security)):
        """Verify JWT token."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated"
            )
        
        token = credentials.credentials
        token_data = verify_token(token)
        
        # Store user info in request state
        request.state.user_id = token_data.user_id
        request.state.user_email = token_data.email
        
        return token_data


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> User:
    """
    Get current authenticated user.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User object
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    # Fetch user from database
    from agent_factory.database.models import User as UserModel
    from agent_factory.database.session import get_db
    
    db = next(get_db())
    try:
        user_model = db.query(UserModel).filter(UserModel.id == token_data.user_id).first()
        
        if not user_model:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is unavailable",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user_model.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = User(
            id=str(user_model.id),
            email=str(user_model.email or ""),
            roles=user_model.roles or [],
            permissions=user_model.permissions or [],
            tenant_id=user_model.tenant_id,
        )
        request.state.user_id = user.id
        request.state.tenant_id = user.tenant_id
        
        return user
    finally:
        db.close()


async def get_current_user_from_request(request: Request) -> User | None:
    """
    Get current authenticated user from request (supports both JWT and API keys).
    
    Args:
        request: FastAPI request
        
    Returns:
        User object or None if not authenticated
    """
    # Check for API key first
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if api_key and api_key.startswith("af_"):
        # API key authentication
        from agent_factory.auth.api_keys import verify_api_key
        
        key_info = verify_api_key(api_key)
        if key_info:
            from agent_factory.database.models import User as UserModel
            from agent_factory.database.session import get_db
            
            db = next(get_db())
            try:
                user_model = db.query(UserModel).filter(UserModel.id == key_info["user_id"]).first()
                if user_model:
                    user = User(
                        id=str(user_model.id),
                        email=str(user_model.email or ""),
                        roles=user_model.roles or [],
                        permissions=key_info.get("permissions", user_model.permissions or []),
                    )
                    # Store tenant_id in request state
                    request.state.tenant_id = key_info["tenant_id"]
                    request.state.user_id = user.id
                    return user
            finally:
                db.close()
        
        return None
    
    # Fall back to JWT authentication
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            token_data = verify_token(token)
            
            from agent_factory.database.models import User as UserModel
            from agent_factory.database.session import get_db
            
            db = next(get_db())
            try:
                user_model = db.query(UserModel).filter(UserModel.id == token_data.user_id).first()
                if user_model:
                    user = User(
                        id=str(user_model.id),
                        email=str(user_model.email or ""),
                        roles=user_model.roles or [],
                        permissions=user_model.permissions or [],
                    )
                    request.state.tenant_id = user_model.tenant_id
                    request.state.user_id = user.id
                    return user
            finally:
                db.close()
        except Exception:  # nosec B110 -- db.close() in a cleanup path; a close failure must not mask the exception already propagating
            pass
    
    return None
