"""
Database repository for Oneline Chat data persistence.
"""

from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from .models import OnelineChat, AgentMarketplace, AgentAccess, ModeEnum, AgentCommunicationProtocol, User, UserSession


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


class UserRepository:
    """Repository for handling user authentication operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    # User operations
    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None
    ) -> User:
        """Create a new user."""
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            created_at=datetime.utcnow()
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        statement = select(User).where(User.email == email)
        results = self.session.exec(statement)
        return results.first()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        statement = select(User).where(User.username == username)
        results = self.session.exec(statement)
        return results.first()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        statement = select(User).where(User.id == user_id)
        results = self.session.exec(statement)
        return results.first()
    
    async def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        statement = select(User).where(User.id == user_id)
        user = self.session.exec(statement).first()
        if user:
            user.last_login = datetime.utcnow()
            self.session.add(user)
            self.session.commit()
            return True
        return False
    
    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user profile information."""
        statement = select(User).where(User.id == user_id)
        user = self.session.exec(statement).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user
        return None
    
    # Session operations
    async def create_session(
        self,
        user_id: int,
        session_token: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        """Create a new user session."""
        session = UserSession(
            session_token=session_token,
            user_id=user_id,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            user_agent=user_agent,
            ip_address=ip_address
        )
        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        return session
    
    async def get_session(self, token: str) -> Optional[UserSession]:
        """Get a session by token."""
        statement = select(UserSession).where(
            UserSession.session_token == token,
            UserSession.expires_at > datetime.utcnow()
        )
        results = self.session.exec(statement)
        return results.first()
    
    async def delete_session(self, token: str) -> bool:
        """Delete a session (logout)."""
        statement = select(UserSession).where(UserSession.session_token == token)
        session = self.session.exec(statement).first()
        if session:
            self.session.delete(session)
            self.session.commit()
            return True
        return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from database."""
        statement = select(UserSession).where(UserSession.expires_at <= datetime.utcnow())
        expired_sessions = self.session.exec(statement).all()
        count = len(expired_sessions)
        for session in expired_sessions:
            self.session.delete(session)
        self.session.commit()
        return count
    
    async def get_user_sessions(self, user_id: int) -> List[UserSession]:
        """Get all active sessions for a user."""
        statement = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.expires_at > datetime.utcnow()
        )
        results = self.session.exec(statement)
        return results.all()
    
    async def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user (logout from all devices)."""
        statement = select(UserSession).where(UserSession.user_id == user_id)
        sessions = self.session.exec(statement).all()
        count = len(sessions)
        for session in sessions:
            self.session.delete(session)
        self.session.commit()
        return count