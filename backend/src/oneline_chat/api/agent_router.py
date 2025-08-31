"""
Agent management API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlmodel import Session

from ..db import get_session
from ..db.models import (
    Agent, AgentResponse, AgentListResponse,
    ChatSession, AgentMessage
)
from ..services.agent_registry import agent_registry, AgentConfig, AgentStatus
from ..core.logging import get_logger
from .auth_router import get_optional_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


async def initialize_agents():
    """Initialize agent registry."""
    try:
        await agent_registry.initialize()
        logger.info("Agent registry initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent registry: {e}")
        # Don't raise here, let the endpoints handle missing agents gracefully


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup agent registry on shutdown."""
    await agent_registry.cleanup()
    logger.info("Agent registry cleaned up")


@router.get("", response_model=AgentListResponse)
async def list_agents(
    include_offline: bool = Query(default=False, description="Include offline agents"),
    capability: Optional[str] = Query(default=None, description="Filter by capability"),
    db: Session = Depends(get_session),
    current_user = Depends(get_optional_user)
):
    """
    List all available agents.
    
    Args:
        include_offline: Whether to include offline agents
        capability: Optional capability filter
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        List of available agents
    """
    try:
        # Ensure agent registry is initialized
        if not agent_registry._initialized:
            await agent_registry.initialize()
        
        if capability:
            agents = agent_registry.list_agents_by_capability(capability)
        else:
            agents = agent_registry.list_agents(include_offline=include_offline)
        
        agent_responses = []
        for agent in agents:
            agent_responses.append(AgentResponse(
                id=agent.id,
                name=agent.name,
                type=agent.type.value if hasattr(agent.type, 'value') else agent.type,
                provider=agent.provider.value if hasattr(agent.provider, 'value') else agent.provider,
                model=agent.model,
                description=agent.description,
                capabilities=agent.capabilities,
                avatar_url=agent.avatar_url,
                status=agent.status.value if hasattr(agent.status, 'value') else agent.status,
                last_health_check=agent.last_health_check,
                response_time_ms=agent.response_time_ms,
            ))
        
        online_count = len([a for a in agents if a.status == AgentStatus.ONLINE])
        
        return AgentListResponse(
            agents=agent_responses,
            total=len(agent_responses),
            online_count=online_count
        )
    
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_session),
    current_user = Depends(get_optional_user)
):
    """
    Get details of a specific agent.
    
    Args:
        agent_id: Agent identifier
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        Agent details
    """
    try:
        # Ensure agent registry is initialized
        if not agent_registry._initialized:
            await agent_registry.initialize()
        
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Check current status
        await agent_registry.check_agent_status(agent_id)
        
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type.value if hasattr(agent.type, 'value') else agent.type,
            provider=agent.provider.value if hasattr(agent.provider, 'value') else agent.provider,
            model=agent.model,
            description=agent.description,
            capabilities=agent.capabilities,
            avatar_url=agent.avatar_url,
            status=agent.status.value if hasattr(agent.status, 'value') else agent.status,
            last_health_check=agent.last_health_check,
            response_time_ms=agent.response_time_ms,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/status")
async def check_agent_status(
    agent_id: str,
    db: Session = Depends(get_session),
    current_user = Depends(get_optional_user)
):
    """
    Check the current status of an agent.
    
    Args:
        agent_id: Agent identifier
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        Agent status
    """
    try:
        status = await agent_registry.check_agent_status(agent_id)
        return {
            "agent_id": agent_id,
            "status": status.value if hasattr(status, 'value') else status
        }
    
    except Exception as e:
        logger.error(f"Error checking agent status {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/select")
async def select_agent_for_chat(
    agent_id: str,
    chat_id: str,
    db: Session = Depends(get_session),
    current_user = Depends(get_optional_user)
):
    """
    Select an agent for the current chat session.
    
    Args:
        agent_id: Agent identifier to select
        chat_id: Chat session identifier
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        Success status
    """
    try:
        # Verify agent exists and is online
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        if agent.status != AgentStatus.ONLINE:
            raise HTTPException(status_code=400, detail=f"Agent {agent_id} is not available")
        
        # Update or create chat session
        from sqlmodel import select
        statement = select(ChatSession).where(ChatSession.chat_id == chat_id)
        result = db.exec(statement)
        chat_session = result.first()
        if not chat_session:
            chat_session = ChatSession(
                chat_id=chat_id,
                user_id=str(current_user.id) if current_user else None,
                active_agent_id=agent_id,
                agent_history=[agent_id]
            )
            db.add(chat_session)
        else:
            chat_session.active_agent_id = agent_id
            if chat_session.agent_history is None:
                chat_session.agent_history = []
            if agent_id not in chat_session.agent_history:
                chat_session.agent_history.append(agent_id)
        
        db.commit()
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "message": f"Agent {agent.name} selected for chat"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting agent {agent_id} for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{chat_id}/active")
async def get_active_agent(
    chat_id: str,
    db: Session = Depends(get_session),
    current_user = Depends(get_optional_user)
):
    """
    Get the currently active agent for a chat session.
    
    Args:
        chat_id: Chat session identifier
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        Active agent information
    """
    try:
        # Get chat session
        from sqlmodel import select
        statement = select(ChatSession).where(ChatSession.chat_id == chat_id)
        result = db.exec(statement)
        chat_session = result.first()
        
        if not chat_session or not chat_session.active_agent_id:
            # Return default agent if no active agent
            default_agent = agent_registry.get_default_agent()
            if default_agent:
                return {
                    "agent_id": default_agent.id,
                    "agent_name": default_agent.name,
                    "is_default": True
                }
            else:
                raise HTTPException(status_code=404, detail="No agents available")
        
        agent = agent_registry.get_agent(chat_session.active_agent_id)
        if not agent:
            # Fallback to default if active agent not found
            default_agent = agent_registry.get_default_agent()
            if default_agent:
                return {
                    "agent_id": default_agent.id,
                    "agent_name": default_agent.name,
                    "is_default": True
                }
            else:
                raise HTTPException(status_code=404, detail="Active agent not found")
        
        return {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "is_default": False
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active agent for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default")
async def get_default_agent(
    db: Session = Depends(get_session),
    current_user = Depends(get_optional_user)
):
    """
    Get the default agent.
    
    Args:
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        Default agent information
    """
    try:
        # Ensure agent registry is initialized
        if not agent_registry._initialized:
            await agent_registry.initialize()
        
        default_agent = agent_registry.get_default_agent()
        if not default_agent:
            raise HTTPException(status_code=404, detail="No default agent available")
        
        return AgentResponse(
            id=default_agent.id,
            name=default_agent.name,
            type=default_agent.type.value if hasattr(default_agent.type, 'value') else default_agent.type,
            provider=default_agent.provider.value if hasattr(default_agent.provider, 'value') else default_agent.provider,
            model=default_agent.model,
            description=default_agent.description,
            capabilities=default_agent.capabilities,
            avatar_url=default_agent.avatar_url,
            status=default_agent.status.value if hasattr(default_agent.status, 'value') else default_agent.status,
            last_health_check=default_agent.last_health_check,
            response_time_ms=default_agent.response_time_ms,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))