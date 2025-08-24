"""
Database repository for Oneline Chat data persistence.
"""

from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from .models import OnelineChat, AgentMarketplace, AgentAccess, ModeEnum, AgentCommunicationProtocol


class PersistenceRepository:
    """Repository for handling database operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    # OnelineChat operations
    def create_chat(
        self,
        chat_id: str,
        message_id: str,
        question: str,
        response: str,
        mode: ModeEnum,
        agents: Optional[dict] = None
    ) -> OnelineChat:
        """Create a new chat message record."""
        chat = OnelineChat(
            chat_id=chat_id,
            message_id=message_id,
            question=question,
            response=response,
            mode=mode,
            agents=agents,
            msg_timestamp=datetime.utcnow()
        )
        self.session.add(chat)
        self.session.commit()
        self.session.refresh(chat)
        return chat
    
    def get_chat_by_id(self, chat_id: str) -> List[OnelineChat]:
        """Get all messages for a specific chat session."""
        statement = select(OnelineChat).where(OnelineChat.chat_id == chat_id)
        results = self.session.exec(statement)
        return results.all()
    
    def get_chat_by_message_id(self, message_id: str) -> Optional[OnelineChat]:
        """Get a specific message by its ID."""
        statement = select(OnelineChat).where(OnelineChat.message_id == message_id)
        results = self.session.exec(statement)
        return results.first()
    
    # AgentMarketplace operations
    def create_agent(
        self,
        agent_name: str,
        agent_display_name: str,
        protocol: AgentCommunicationProtocol
    ) -> AgentMarketplace:
        """Create a new agent in the marketplace."""
        agent = AgentMarketplace(
            agent_name=agent_name,
            agent_display_name=agent_display_name,
            agent_communication_protocol=protocol
        )
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent
    
    def get_agent_by_name(self, agent_name: str) -> Optional[AgentMarketplace]:
        """Get an agent by its name."""
        statement = select(AgentMarketplace).where(AgentMarketplace.agent_name == agent_name)
        results = self.session.exec(statement)
        return results.first()
    
    def get_all_agents(self) -> List[AgentMarketplace]:
        """Get all available agents."""
        statement = select(AgentMarketplace)
        results = self.session.exec(statement)
        return results.all()
    
    # AgentAccess operations
    def grant_agent_access(self, username: str, agent_id: int) -> AgentAccess:
        """Grant a user access to an agent."""
        access = AgentAccess(
            username=username,
            agent_id=agent_id
        )
        self.session.add(access)
        self.session.commit()
        self.session.refresh(access)
        return access
    
    def get_user_agents(self, username: str) -> List[AgentMarketplace]:
        """Get all agents a user has access to."""
        statement = select(AgentAccess).where(AgentAccess.username == username)
        accesses = self.session.exec(statement).all()
        
        agents = []
        for access in accesses:
            agent_statement = select(AgentMarketplace).where(AgentMarketplace.id == access.agent_id)
            agent = self.session.exec(agent_statement).first()
            if agent:
                agents.append(agent)
        return agents
    
    def check_user_agent_access(self, username: str, agent_id: int) -> bool:
        """Check if a user has access to a specific agent."""
        statement = select(AgentAccess).where(
            AgentAccess.username == username,
            AgentAccess.agent_id == agent_id
        )
        result = self.session.exec(statement).first()
        return result is not None
    
    def revoke_agent_access(self, username: str, agent_id: int) -> bool:
        """Revoke a user's access to an agent."""
        statement = select(AgentAccess).where(
            AgentAccess.username == username,
            AgentAccess.agent_id == agent_id
        )
        access = self.session.exec(statement).first()
        if access:
            self.session.delete(access)
            self.session.commit()
            return True
        return False