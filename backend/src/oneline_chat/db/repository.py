"""
Database repository for Oneline Chat data persistence.
"""

from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from .models import OnelineChat, AgentMarketplace, AgentAccess, ModeEnum, AgentCommunicationProtocol, User, UserSession, ChatSummary, ChatHistoryResponse, SharedChat, ShareSettings, ShareResponse, SharedChatResponse


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
        agents: Optional[dict] = None,
        chat_title: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> OnelineChat:
        """Create a new chat message record."""
        now = datetime.utcnow()
        
        # Auto-generate title from question if not provided
        if not chat_title and question:
            chat_title = question[:50] + "..." if len(question) > 50 else question
        
        chat = OnelineChat(
            chat_id=chat_id,
            message_id=message_id,
            question=question,
            response=response,
            mode=mode,
            agents=agents,
            msg_timestamp=now,
            chat_title=chat_title,
            user_id=user_id,
            created_at=now,
            updated_at=now
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
    
    # Chat History operations
    def get_all_chats(
        self, 
        user_id: Optional[str] = None, 
        limit: int = 50, 
        offset: int = 0,
        search_query: Optional[str] = None
    ) -> List[ChatSummary]:
        """Get all chat sessions with summary information."""
        # Base query to get unique chat sessions
        base_query = select(OnelineChat.chat_id).distinct()
        
        # Add user filter if provided
        if user_id:
            base_query = base_query.where(OnelineChat.user_id == user_id)
        
        # Add soft delete filter
        base_query = base_query.where(OnelineChat.is_deleted == False)
        
        # Add search filter if provided
        if search_query:
            base_query = base_query.where(
                OnelineChat.question.ilike(f"%{search_query}%") |
                OnelineChat.response.ilike(f"%{search_query}%") |
                OnelineChat.chat_title.ilike(f"%{search_query}%")
            )
        
        # Get unique chat_ids
        chat_ids_result = self.session.exec(base_query.limit(limit).offset(offset))
        chat_ids = chat_ids_result.all()
        
        chat_summaries = []
        
        for chat_id in chat_ids:
            # Get chat summary data
            summary_query = select(
                OnelineChat.chat_id,
                OnelineChat.chat_title,
                OnelineChat.created_at,
                OnelineChat.updated_at,
                OnelineChat.question,
                OnelineChat.agents
            ).where(
                OnelineChat.chat_id == chat_id,
                OnelineChat.is_deleted == False
            ).order_by(OnelineChat.msg_timestamp.desc()).limit(1)
            
            latest_message = self.session.exec(summary_query).first()
            
            if latest_message:
                # Count messages in this chat
                count_query = select(OnelineChat).where(
                    OnelineChat.chat_id == chat_id,
                    OnelineChat.is_deleted == False
                )
                message_count = len(self.session.exec(count_query).all())
                
                # Get model used from agents data
                model_used = None
                if latest_message.agents and isinstance(latest_message.agents, dict):
                    model_used = latest_message.agents.get('model')
                
                # Create preview from question (truncate if too long)
                preview = latest_message.question
                if len(preview) > 100:
                    preview = preview[:97] + "..."
                
                chat_summaries.append(ChatSummary(
                    chat_id=latest_message.chat_id,
                    chat_title=latest_message.chat_title or preview,
                    last_message_preview=preview,
                    message_count=message_count,
                    created_at=latest_message.created_at,
                    updated_at=latest_message.updated_at,
                    model_used=model_used
                ))
        
        # Sort by updated_at descending
        chat_summaries.sort(key=lambda x: x.updated_at, reverse=True)
        
        return chat_summaries
    
    def get_chat_history_with_messages(self, chat_id: str, user_id: Optional[str] = None) -> Optional[ChatHistoryResponse]:
        """Get full chat history with all messages."""
        # Build query
        query = select(OnelineChat).where(
            OnelineChat.chat_id == chat_id,
            OnelineChat.is_deleted == False
        )
        
        # Add user filter if provided
        if user_id:
            query = query.where(OnelineChat.user_id == user_id)
        
        query = query.order_by(OnelineChat.msg_timestamp.asc())
        
        messages = self.session.exec(query).all()
        
        if not messages:
            return None
        
        # Format messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "message_id": msg.message_id,
                "question": msg.question,
                "response": msg.response,
                "timestamp": msg.msg_timestamp.isoformat(),
                "mode": msg.mode.value,
                "agents": msg.agents
            })
        
        return ChatHistoryResponse(
            chat_id=chat_id,
            chat_title=messages[0].chat_title,
            created_at=messages[0].created_at,
            updated_at=messages[-1].updated_at,
            messages=formatted_messages
        )
    
    def delete_chat(self, chat_id: str, user_id: Optional[str] = None) -> bool:
        """Soft delete a chat session."""
        # Build query
        query = select(OnelineChat).where(OnelineChat.chat_id == chat_id)
        
        # Add user filter if provided
        if user_id:
            query = query.where(OnelineChat.user_id == user_id)
        
        messages = self.session.exec(query).all()
        
        if not messages:
            return False
        
        # Mark all messages in the chat as deleted
        for message in messages:
            message.is_deleted = True
            self.session.add(message)
        
        self.session.commit()
        return True
    
    def update_chat_title(self, chat_id: str, title: str, user_id: Optional[str] = None) -> bool:
        """Update chat title for all messages in a chat session."""
        # Build query
        query = select(OnelineChat).where(
            OnelineChat.chat_id == chat_id,
            OnelineChat.is_deleted == False
        )
        
        # Add user filter if provided
        if user_id:
            query = query.where(OnelineChat.user_id == user_id)
        
        messages = self.session.exec(query).all()
        
        if not messages:
            return False
        
        # Update title for all messages in the chat
        for message in messages:
            message.chat_title = title
            message.updated_at = datetime.utcnow()
            self.session.add(message)
        
        self.session.commit()
        return True
    
    def get_chat_summary(self, chat_id: str, user_id: Optional[str] = None) -> Optional[ChatSummary]:
        """Get summary information for a specific chat."""
        # Build query for latest message
        query = select(OnelineChat).where(
            OnelineChat.chat_id == chat_id,
            OnelineChat.is_deleted == False
        )
        
        # Add user filter if provided
        if user_id:
            query = query.where(OnelineChat.user_id == user_id)
        
        query = query.order_by(OnelineChat.msg_timestamp.desc()).limit(1)
        
        latest_message = self.session.exec(query).first()
        
        if not latest_message:
            return None
        
        # Count messages in this chat
        count_query = select(OnelineChat).where(
            OnelineChat.chat_id == chat_id,
            OnelineChat.is_deleted == False
        )
        if user_id:
            count_query = count_query.where(OnelineChat.user_id == user_id)
        
        message_count = len(self.session.exec(count_query).all())
        
        # Get model used from agents data
        model_used = None
        if latest_message.agents and isinstance(latest_message.agents, dict):
            model_used = latest_message.agents.get('model')
        
        # Create preview from question
        preview = latest_message.question
        if len(preview) > 100:
            preview = preview[:97] + "..."
        
        return ChatSummary(
            chat_id=latest_message.chat_id,
            chat_title=latest_message.chat_title or preview,
            last_message_preview=preview,
            message_count=message_count,
            created_at=latest_message.created_at,
            updated_at=latest_message.updated_at,
            model_used=model_used
        )
    
    # Shared Chat operations
    def create_shared_chat(
        self, 
        share_token: str,
        chat_id: str, 
        owner_id: str, 
        settings: ShareSettings
    ) -> SharedChat:
        """Create a new shared chat."""
        shared_chat = SharedChat(
            share_token=share_token,
            chat_id=chat_id,
            owner_id=owner_id,
            title=settings.title,
            description=settings.description,
            is_public=settings.is_public,
            expires_at=settings.expires_at,
            view_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(shared_chat)
        self.session.commit()
        self.session.refresh(shared_chat)
        return shared_chat
    
    def get_shared_chat_by_token(self, share_token: str) -> Optional[SharedChat]:
        """Get a shared chat by its share token."""
        statement = select(SharedChat).where(
            SharedChat.share_token == share_token,
            SharedChat.is_public == True
        )
        # Check if not expired
        now = datetime.utcnow()
        statement = statement.where(
            (SharedChat.expires_at.is_(None)) | (SharedChat.expires_at > now)
        )
        result = self.session.exec(statement)
        return result.first()
    
    def get_shared_chat_by_chat_id(self, chat_id: str, owner_id: str) -> Optional[SharedChat]:
        """Get shared chat info by chat_id and owner."""
        statement = select(SharedChat).where(
            SharedChat.chat_id == chat_id,
            SharedChat.owner_id == owner_id
        )
        result = self.session.exec(statement)
        return result.first()
    
    def increment_view_count(self, share_token: str) -> bool:
        """Increment view count for a shared chat."""
        statement = select(SharedChat).where(SharedChat.share_token == share_token)
        shared_chat = self.session.exec(statement).first()
        if shared_chat:
            shared_chat.view_count += 1
            shared_chat.updated_at = datetime.utcnow()
            self.session.add(shared_chat)
            self.session.commit()
            return True
        return False
    
    def delete_shared_chat(self, chat_id: str, owner_id: str) -> bool:
        """Delete/unshare a chat."""
        statement = select(SharedChat).where(
            SharedChat.chat_id == chat_id,
            SharedChat.owner_id == owner_id
        )
        shared_chat = self.session.exec(statement).first()
        if shared_chat:
            self.session.delete(shared_chat)
            self.session.commit()
            return True
        return False
    
    def update_shared_chat(
        self, 
        chat_id: str, 
        owner_id: str, 
        settings: ShareSettings
    ) -> Optional[SharedChat]:
        """Update shared chat settings."""
        statement = select(SharedChat).where(
            SharedChat.chat_id == chat_id,
            SharedChat.owner_id == owner_id
        )
        shared_chat = self.session.exec(statement).first()
        if shared_chat:
            shared_chat.title = settings.title
            shared_chat.description = settings.description
            shared_chat.is_public = settings.is_public
            shared_chat.expires_at = settings.expires_at
            shared_chat.updated_at = datetime.utcnow()
            self.session.add(shared_chat)
            self.session.commit()
            self.session.refresh(shared_chat)
            return shared_chat
        return None


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