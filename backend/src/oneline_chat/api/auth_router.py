"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from ..db.database import get_session
from ..db.repository import UserRepository
from ..db.models import User
from ..core.auth_utils import (
    hash_password,
    verify_password,
    generate_session_token,
    create_access_token,
    create_session_expiry
)
from sqlmodel import Session


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
security = HTTPBearer()


# Pydantic models for request/response
class UserRegister(BaseModel):
    """User registration request model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)


class UserLogin(BaseModel):
    """User login request model."""
    username_or_email: str
    password: str
    remember_me: bool = False


class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


class LoginResponse(BaseModel):
    """Login response model."""
    user: UserResponse
    session_token: str
    expires_at: datetime


class UserUpdate(BaseModel):
    """User profile update model."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """Password change request model."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# Dependency to get current user from session token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """Get current user from bearer token."""
    token = credentials.credentials
    user_repo = UserRepository(session)
    
    # Get session
    user_session = await user_repo.get_session(token)
    if not user_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = await user_repo.get_user_by_id(user_session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# Optional dependency - returns user if authenticated, None otherwise
async def get_optional_user(
    request: Request,
    session: Session = Depends(get_session)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    user_repo = UserRepository(session)
    
    user_session = await user_repo.get_session(token)
    if not user_session:
        return None
    
    user = await user_repo.get_user_by_id(user_session.user_id)
    return user if user and user.is_active else None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    session: Session = Depends(get_session)
):
    """Register a new user."""
    user_repo = UserRepository(session)
    
    # Check if username already exists
    existing_user = await user_repo.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_user = await user_repo.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    password_hash = hash_password(user_data.password)
    user = await user_repo.create_user(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name
    )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    credentials: UserLogin,
    request: Request,
    session: Session = Depends(get_session)
):
    """Authenticate user and create session."""
    user_repo = UserRepository(session)
    
    # Find user by username or email
    user = None
    if "@" in credentials.username_or_email:
        user = await user_repo.get_user_by_email(credentials.username_or_email)
    else:
        user = await user_repo.get_user_by_username(credentials.username_or_email)
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create session
    session_token = generate_session_token()
    expires_at = create_session_expiry(credentials.remember_me)
    
    # Get user agent and IP
    user_agent = request.headers.get("User-Agent")
    client_host = request.client.host if request.client else None
    
    await user_repo.create_session(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=client_host
    )
    
    # Update last login
    await user_repo.update_last_login(user.id)
    
    return LoginResponse(
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=datetime.utcnow()
        ),
        session_token=session_token,
        expires_at=expires_at
    )


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """Logout current user by deleting session."""
    user_repo = UserRepository(session)
    token = credentials.credentials
    
    deleted = await user_repo.delete_session(token)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session not found"
        )
    
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update current user profile."""
    user_repo = UserRepository(session)
    
    # Check if new email is already taken
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = await user_repo.get_user_by_email(profile_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    # Update user
    update_data = {}
    if profile_data.full_name is not None:
        update_data["full_name"] = profile_data.full_name
    if profile_data.email is not None:
        update_data["email"] = profile_data.email
    
    if update_data:
        user = await user_repo.update_user(current_user.id, **update_data)
    else:
        user = current_user
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Change current user's password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password and update
    user_repo = UserRepository(session)
    new_password_hash = hash_password(password_data.new_password)
    await user_repo.update_user(current_user.id, password_hash=new_password_hash)
    
    # Optionally, invalidate all existing sessions except current
    # await user_repo.delete_user_sessions(current_user.id)
    
    return MessageResponse(message="Password changed successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Logout from all devices by deleting all sessions."""
    user_repo = UserRepository(session)
    count = await user_repo.delete_user_sessions(current_user.id)
    
    return MessageResponse(message=f"Logged out from {count} sessions")