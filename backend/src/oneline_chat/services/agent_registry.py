"""
Agent Registry Service for managing multiple AI agents.
"""

import asyncio
import httpx
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

from ..core.logging import get_logger
from ..core.config import settings

logger = get_logger(__name__)


class AgentStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class AgentType(str, Enum):
    SYSTEM = "system"
    CUSTOM = "custom"
    SPECIALIZED = "specialized"


class AgentProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    CUSTOM = "custom"


class AgentConfig:
    """Configuration for an AI agent."""
    
    def __init__(
        self,
        id: str,
        name: str,
        type: AgentType,
        provider: AgentProvider,
        model: str,
        description: str = "",
        capabilities: List[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        avatar_url: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        self.id = id
        self.name = name
        self.type = type
        self.provider = provider
        self.model = model
        self.description = description
        self.capabilities = capabilities or []
        self.base_url = base_url
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.parameters = parameters or {}
        self.avatar_url = avatar_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.status = AgentStatus.OFFLINE
        self.last_health_check = None
        self.response_time_ms = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent config to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "provider": self.provider.value if isinstance(self.provider, Enum) else self.provider,
            "model": self.model,
            "description": self.description,
            "capabilities": self.capabilities,
            "base_url": self.base_url,
            "system_prompt": self.system_prompt,
            "parameters": self.parameters,
            "avatar_url": self.avatar_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "response_time_ms": self.response_time_ms,
        }


class AgentRegistry:
    """Registry for managing multiple AI agents."""
    
    def __init__(self):
        self.agents: Dict[str, AgentConfig] = {}
        self._initialized = False
        self._health_check_task = None
        
    async def initialize(self):
        """Initialize the registry with default agents."""
        if self._initialized:
            return
            
        # Register default system agents
        await self._register_default_agents()
        
        # Start health check background task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        self._initialized = True
        logger.info(f"Agent registry initialized with {len(self.agents)} agents")
    
    async def _register_default_agents(self):
        """Register agents from the agents directory only."""
        # Only discover agents running as separate services
        await self._discover_agents_from_directory()
    
    async def _discover_agents_from_directory(self):
        """Discover and register agents from the agents directory."""
        import os
        from pathlib import Path
        
        # Look for agents directory relative to project root
        # Go up 4 levels: services -> oneline_chat -> src -> backend -> project_root
        current_dir = Path(__file__).parent.parent.parent.parent.parent
        agents_dir = current_dir / "agents"
        
        # Check if agents directory exists
        if not agents_dir.exists():
            logger.warning(f"Agents directory '{agents_dir}' not found")
            return
        
        # Define known agents in the agents directory
        known_agents = [
            {
                "id": "brd-agent",
                "name": "BRD Specialist",
                "port": 8001,
                "description": "Business Requirements Document specialist - helps create comprehensive business requirements",
                "capabilities": ["business-analysis", "requirements-gathering", "documentation", "stakeholder-analysis"],
                "avatar_url": "📋",
                "directory": "brd_agent"
            },
            {
                "id": "prd-agent", 
                "name": "PRD Specialist",
                "port": 8002,
                "description": "Product Requirements Document specialist - creates technical product specifications",
                "capabilities": ["product-specs", "technical-requirements", "api-documentation", "feature-planning"],
                "avatar_url": "📝",
                "directory": "prd_agent"
            },
        ]
        
        for agent_info in known_agents:
            agent_dir = agents_dir / agent_info["directory"]
            
            # Check if agent directory exists
            if not agent_dir.exists():
                logger.info(f"Agent directory '{agent_dir}' not found, skipping {agent_info['name']}")
                continue
            
            base_url = f"http://localhost:{agent_info['port']}"
            
            # Check if agent is running
            if await self._check_agent_health(base_url):
                self.register_agent(AgentConfig(
                    id=agent_info["id"],
                    name=agent_info["name"],
                    type=AgentType.SPECIALIZED,
                    provider=AgentProvider.CUSTOM,
                    model=agent_info["id"],  # Use agent ID as model name
                    description=agent_info["description"],
                    capabilities=agent_info["capabilities"],
                    base_url=base_url,
                    avatar_url=agent_info["avatar_url"],
                    max_tokens=4096,
                    temperature=0.7,
                ))
                logger.info(f"Registered agent: {agent_info['name']} at {base_url}")
            else:
                logger.info(f"Agent {agent_info['name']} not running at {base_url} (directory exists but service unavailable)")
        
        if len(self.agents) == 0:
            logger.warning("No agents discovered! Make sure agents are running:")
            for agent_info in known_agents:
                logger.warning(f"  - Start {agent_info['name']}: cd agents/{agent_info['directory']} && python {agent_info['directory']}.py")
    
    def register_agent(self, agent: AgentConfig) -> bool:
        """Register a new agent."""
        if agent.id in self.agents:
            logger.warning(f"Agent {agent.id} already registered, updating configuration")
        
        self.agents[agent.id] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.id})")
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id not in self.agents:
            return False
        
        del self.agents[agent_id]
        logger.info(f"Unregistered agent: {agent_id}")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self, include_offline: bool = False) -> List[AgentConfig]:
        """List all registered agents."""
        agents = list(self.agents.values())
        if not include_offline:
            agents = [a for a in agents if a.status != AgentStatus.OFFLINE]
        return agents
    
    def list_agents_by_capability(self, capability: str) -> List[AgentConfig]:
        """List agents with a specific capability."""
        return [
            agent for agent in self.agents.values()
            if capability in agent.capabilities and agent.status == AgentStatus.ONLINE
        ]
    
    async def _check_agent_health(self, base_url: str) -> bool:
        """Check if an agent service is healthy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/health",
                    timeout=httpx.Timeout(5.0)
                )
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed for {base_url}: {e}")
            return False
    
    async def check_agent_status(self, agent_id: str) -> AgentStatus:
        """Check the current status of an agent."""
        agent = self.get_agent(agent_id)
        if not agent:
            return AgentStatus.OFFLINE
        
        # For system agents, check API key availability
        if agent.type == AgentType.SYSTEM:
            if agent.provider == AgentProvider.OPENAI and not agent.api_key:
                agent.status = AgentStatus.OFFLINE
            elif agent.provider == AgentProvider.ANTHROPIC and not agent.api_key:
                agent.status = AgentStatus.OFFLINE
            else:
                agent.status = AgentStatus.ONLINE
        
        # For specialized agents, check health endpoint
        elif agent.type == AgentType.SPECIALIZED and agent.base_url:
            if await self._check_agent_health(agent.base_url):
                agent.status = AgentStatus.ONLINE
            else:
                agent.status = AgentStatus.OFFLINE
        
        agent.last_health_check = datetime.utcnow()
        return agent.status
    
    async def _health_check_loop(self):
        """Background task to periodically check agent health."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                for agent_id in list(self.agents.keys()):
                    await self.check_agent_status(agent_id)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    def get_default_agent(self) -> Optional[AgentConfig]:
        """Get the default agent based on configuration."""
        # Try to get the configured default model
        default_model = settings.ai.default_model
        
        # Map common model names to agent IDs
        model_to_agent = {
            "gpt-4": "gpt-4",
            "gpt-4o": "gpt-4o",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "claude-3-5-sonnet-20241022": "claude-3-5-sonnet",
            "llama3.1:latest": "llama3",
        }
        
        agent_id = model_to_agent.get(default_model)
        if agent_id and agent_id in self.agents:
            return self.agents[agent_id]
        
        # Return first available online agent
        for agent in self.agents.values():
            if agent.status == AgentStatus.ONLINE:
                return agent
        
        return None
    
    async def cleanup(self):
        """Cleanup resources."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass


# Global registry instance
agent_registry = AgentRegistry()