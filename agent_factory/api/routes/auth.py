"""
Authentication API Routes.

Provides:
- User signup (email + password)
- User login (email + password, returns JWT)
- Magic link (stub for future)
"""

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, validator

if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("about", (), {"__version__": getattr(bcrypt, "__version__", "4.0.0")})()

import uuid

from passlib.context import CryptContext

from agent_factory.database.models import Tenant
from agent_factory.database.models import User as UserModel
from agent_factory.database.session import get_db
from agent_factory.security.auth import create_access_token, verify_token

router = APIRouter()
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SignupRequest(BaseModel):
    """User signup request."""
    email: EmailStr
    password: str = None  # Optional for magic link flow
    
    @validator('password')
    def validate_password(cls, v):
        if v is None:
            return v  # Magic link flow
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    tenant_id: str


class UserResponse(BaseModel):
    """User response."""
    id: str
    email: str
    tenant_id: str
    plan: str


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return pwd_context.verify(plain_password, hashed_password)


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    Create a new user account.
    
    PRODUCT ENDPOINT: User registration.
    """
    db = next(get_db())
    try:
        # Check if user exists
        existing_user = db.query(UserModel).filter(UserModel.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create tenant for new user
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            name=f"Tenant for {request.email}",
            slug=f"tenant-{tenant_id[:8]}",
            plan="free",
            resource_quota={},
            usage={},
            is_active=True
        )
        db.add(tenant)
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(request.password) if request.password else ""
        
        user = UserModel(
            id=user_id,
            email=request.email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            tenant_id=tenant_id,
            roles=["user"],
            permissions=["read", "write"]
        )
        db.add(user)
        db.commit()
        
        # Create access token
        token_data = {
            "sub": user_id,
            "email": request.email
        }
        access_token = create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            email=request.email,
            tenant_id=tenant_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {e!s}"
        )
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login user and return JWT token.
    
    PRODUCT ENDPOINT: User authentication.
    """
    db = next(get_db())
    try:
        # Find user
        user = db.query(UserModel).filter(UserModel.email == request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Create access token
        token_data = {
            "sub": user.id,
            "email": user.email
        }
        access_token = create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id or ""
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {e!s}"
        )
    finally:
        db.close()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(credentials: HTTPBearer = Depends(security)):
    """
    Get current authenticated user info.
    
    PRODUCT ENDPOINT: Get user profile.
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    db = next(get_db())
    try:
        user = db.query(UserModel).filter(UserModel.id == token_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get tenant plan
        plan = "free"
        if user.tenant_id:
            tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
            if tenant:
                plan = tenant.plan or "free"
        
        return UserResponse(
            id=user.id,
            email=user.email,
            tenant_id=user.tenant_id or "",
            plan=plan
        )
    finally:
        db.close()
