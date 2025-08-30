"""
Database models for Oneline Chat.
"""

from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel


class ModeEnum(str, Enum):
    """Chat mode enumeration."""
    single = "single"
    multiple = "multiple"


class AgentCommunicationProtocol(str, Enum):
    """Agent communication protocol enumeration."""
    chatcompletion = "chatcompletion"
    responsesagent = "responsesagent"


class User(SQLModel, table=True):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, nullable=False, max_length=50)
    email: str = Field(unique=True, nullable=False, max_length=255)
    password_hash: str = Field(nullable=False, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)
    
    # Relationships
    sessions: List["UserSession"] = Relationship(back_populates="user")


class UserSession(SQLModel, table=True):
    """User session tracking model."""
    
    __tablename__ = "user_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_token: str = Field(unique=True, nullable=False)
    user_id: int = Field(foreign_key="users.id")
    expires_at: datetime = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="sessions")


class OnelineChat(SQLModel, table=True):
    """Chat conversation model."""
    
    __tablename__ = "oneline_chat"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: str = Field(nullable=False, description="Unique chat session identifier")
    message_id: str = Field(nullable=False, description="Unique message identifier")
    question: str = Field(nullable=False, description="User question/input")
    response: str = Field(nullable=False, description="AI assistant response")
    msg_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )
    mode: ModeEnum = Field(nullable=False, description="Chat mode (single/multiple)")
    agents: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Agent configuration and metadata"
    )
    
    # Chat metadata fields
    chat_title: Optional[str] = Field(default=None, max_length=255, description="User-friendly chat name")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Chat creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last message time"
    )
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    
    # User relationship - supports both int (authenticated) and str (anonymous) 
    user_id: Optional[str] = Field(default=None, nullable=True, description="User ID: integer for authenticated users, anon-xyz for anonymous")


class AgentMarketplace(SQLModel, table=True):
    """Agent marketplace model."""
    
    __tablename__ = "agent_marketplace"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_name: str = Field(
        nullable=False,
        unique=True,
        description="Unique agent identifier"
    )
    agent_display_name: str = Field(
        nullable=False,
        description="Human-readable agent name"
    )
    agent_communication_protocol: AgentCommunicationProtocol = Field(
        nullable=False,
        description="Communication protocol used by agent"
    )
    
    agent_accesses: List["AgentAccess"] = Relationship(back_populates="agent")


class AgentAccess(SQLModel, table=True):
    """Agent access control model."""
    
    __tablename__ = "agent_access"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(nullable=False, description="User identifier")
    agent_id: int = Field(
        foreign_key="agent_marketplace.id",
        description="Reference to agent"
    )
    
    agent: Optional[AgentMarketplace] = Relationship(back_populates="agent_accesses")


# Response models for API
class ChatSummary(BaseModel):
    """Chat summary for chat history list."""
    
    chat_id: str
    chat_title: Optional[str]
    last_message_preview: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    model_used: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    """Chat history with messages."""
    
    chat_id: str
    chat_title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]]