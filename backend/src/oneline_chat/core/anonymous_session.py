"""
Anonymous session management for Oneline Chat.
Handles session tracking for non-authenticated users.
"""

import uuid
from fastapi import Request, Response
from typing import Optional

# Cookie name for anonymous session
ANONYMOUS_SESSION_COOKIE = "oneline_chat_session"
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days in seconds

def get_or_create_anonymous_session(request: Request, response: Response) -> str:
    """
    Get existing anonymous session ID from cookie or create a new one.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        Anonymous session ID in format: anon-<uuid>
    """
    # Try to get existing session from cookie
    existing_session = request.cookies.get(ANONYMOUS_SESSION_COOKIE)
    
    if existing_session and existing_session.startswith("anon-"):
        # Valid existing session
        return existing_session
    
    # Create new anonymous session
    session_id = f"anon-{uuid.uuid4().hex[:16]}"
    
    # Set cookie for future requests
    response.set_cookie(
        key=ANONYMOUS_SESSION_COOKIE,
        value=session_id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    
    return session_id

def get_user_identifier(current_user, request: Request, response: Response) -> str:
    """
    Get user identifier for chat persistence.
    
    Args:
        current_user: Authenticated user object or None
        request: FastAPI request object  
        response: FastAPI response object
        
    Returns:
        User identifier: either str(user.id) for authenticated users
        or anon-<session_id> for anonymous users
    """
    if current_user:
        # Store actual user ID as string for authenticated users
        return str(current_user.id)
    else:
        # Store anonymous session ID for non-authenticated users
        return get_or_create_anonymous_session(request, response)

def is_anonymous_user_id(user_id: str) -> bool:
    """
    Check if a user_id represents an anonymous session.
    
    Args:
        user_id: User identifier
        
    Returns:
        True if user_id is anonymous session format
    """
    return isinstance(user_id, str) and user_id.startswith("anon-")