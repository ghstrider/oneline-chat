"""
Database models for Oneline Chat.
"""

from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ModeEnum(str, Enum):
    """Chat mode enumeration."""
    single = "single"
    multiple = "multiple"


class AgentCommunicationProtocol(str, Enum):
    """Agent communication protocol enumeration."""
    chatcompletion = "chatcompletion"
    responsesagent = "responsesagent"


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