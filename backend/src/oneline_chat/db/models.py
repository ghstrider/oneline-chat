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


class SharedChat(SQLModel, table=True):
    """Shared chat model for public chat sharing."""
    
    __tablename__ = "shared_chats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    share_token: str = Field(unique=True, nullable=False, max_length=64, description="Unique token for accessing shared chat")
    chat_id: str = Field(nullable=False, description="ID of the original chat")
    owner_id: str = Field(nullable=False, description="ID of the user who shared the chat")
    title: str = Field(nullable=False, max_length=200, description="Title for the shared chat")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional description")
    is_public: bool = Field(default=True, description="Whether the chat is publicly accessible")
    expires_at: Optional[datetime] = Field(default=None, description="Optional expiration date")
    view_count: int = Field(default=0, description="Number of times the shared chat has been viewed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the share was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


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


class ShareSettings(BaseModel):
    """Share settings for a chat."""
    
    title: str
    description: Optional[str] = None
    is_public: bool = True
    expires_at: Optional[datetime] = None


class ShareResponse(BaseModel):
    """Response when sharing a chat."""
    
    share_token: str
    share_url: str
    title: str
    is_public: bool
    expires_at: Optional[datetime] = None
    created_at: datetime


class SharedChatResponse(BaseModel):
    """Response for accessing a shared chat."""
    
    share_token: str
    chat_id: str
    title: str
    description: Optional[str]
    is_public: bool
    view_count: int
    created_at: datetime
    messages: List[Dict[str, Any]]


class AgentStatusEnum(str, Enum):
    """Agent status enumeration."""
    online = "online"
    offline = "offline"
    busy = "busy"
    error = "error"


class AgentTypeEnum(str, Enum):
    """Agent type enumeration."""
    system = "system"
    custom = "custom"
    specialized = "specialized"


class AgentProviderEnum(str, Enum):
    """Agent provider enumeration."""
    openai = "openai"
    anthropic = "anthropic"
    ollama = "ollama"
    gemini = "gemini"
    custom = "custom"


class Agent(SQLModel, table=True):
    """Agent configuration model."""
    
    __tablename__ = "agents"
    
    id: str = Field(primary_key=True, description="Unique agent identifier")
    name: str = Field(nullable=False, description="Agent display name")
    type: AgentTypeEnum = Field(nullable=False, description="Agent type")
    provider: AgentProviderEnum = Field(nullable=False, description="AI provider")
    model: str = Field(nullable=False, description="Model name/identifier")
    description: Optional[str] = Field(default=None, max_length=500, description="Agent description")
    capabilities: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="List of agent capabilities"
    )
    base_url: Optional[str] = Field(default=None, description="Base URL for custom agents")
    system_prompt: Optional[str] = Field(default=None, description="System prompt for the agent")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Agent-specific parameters"
    )
    avatar_url: Optional[str] = Field(default=None, description="Avatar URL or emoji")
    max_tokens: int = Field(default=4096, description="Maximum tokens for response")
    temperature: float = Field(default=0.7, description="Temperature setting")
    status: AgentStatusEnum = Field(default=AgentStatusEnum.offline, description="Current agent status")
    last_health_check: Optional[datetime] = Field(default=None, description="Last health check timestamp")
    response_time_ms: Optional[int] = Field(default=None, description="Average response time in milliseconds")
    is_active: bool = Field(default=True, description="Whether agent is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(SQLModel, table=True):
    """Extended chat session model for multi-agent support."""
    
    __tablename__ = "chat_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: str = Field(unique=True, nullable=False, description="Unique chat identifier")
    user_id: Optional[str] = Field(default=None, description="User ID")
    active_agent_id: Optional[str] = Field(default=None, description="Currently active agent")
    agent_history: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="List of agents used in this session"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMessage(SQLModel, table=True):
    """Message with agent attribution."""
    
    __tablename__ = "agent_messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: str = Field(unique=True, nullable=False, description="Unique message identifier")
    chat_id: str = Field(nullable=False, description="Chat session identifier")
    agent_id: Optional[str] = Field(default=None, description="Agent that generated this message")
    role: str = Field(nullable=False, description="Message role (user/assistant/system)")
    content: str = Field(nullable=False, description="Message content")
    message_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional metadata"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentResponse(BaseModel):
    """Response model for agent information."""
    
    id: str
    name: str
    type: str
    provider: str
    model: str
    description: Optional[str]
    capabilities: List[str]
    avatar_url: Optional[str]
    status: str
    last_health_check: Optional[datetime]
    response_time_ms: Optional[int]


class AgentListResponse(BaseModel):
    """Response model for list of agents."""
    
    agents: List[AgentResponse]
    total: int
    online_count: int