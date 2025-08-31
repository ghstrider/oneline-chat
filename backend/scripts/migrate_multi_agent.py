"""
Migration script to add multi-agent support tables.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import SQLModel, create_engine, Session
from src.oneline_chat.db.models import (
    Agent, ChatSession, AgentMessage,
    AgentStatusEnum, AgentTypeEnum, AgentProviderEnum
)
from src.oneline_chat.core.config import settings
from src.oneline_chat.core.logging import get_logger

logger = get_logger(__name__)


def create_tables():
    """Create new tables for multi-agent support."""
    
    # Create database URL
    database_url = settings.db.database_url
    
    # Create engine
    engine = create_engine(database_url, echo=True)
    
    logger.info("Creating multi-agent support tables...")
    
    # Create tables that don't exist
    SQLModel.metadata.create_all(engine, checkfirst=True)
    
    logger.info("Tables created successfully!")
    
    # Add default agents to the database
    with Session(engine) as session:
        # Check if agents already exist
        from sqlmodel import select
        statement = select(Agent)
        result = session.exec(statement)
        existing_agents = len(result.all())
        if existing_agents > 0:
            logger.info(f"Found {existing_agents} existing agents, skipping default agent creation")
            return
        
        logger.info("Adding default agents...")
        
        # Add GPT-4 agents if OpenAI API key is configured
        if settings.ai.openai_api_key:
            gpt4 = Agent(
                id="gpt-4",
                name="GPT-4",
                type=AgentTypeEnum.system,
                provider=AgentProviderEnum.openai,
                model="gpt-4",
                description="OpenAI's most capable model for complex reasoning and generation",
                capabilities=["reasoning", "code", "analysis", "creative", "math"],
                avatar_url="🧠",
                max_tokens=8192,
                temperature=0.7,
                status=AgentStatusEnum.online,
                is_active=True
            )
            session.add(gpt4)
            
            gpt4o = Agent(
                id="gpt-4o",
                name="GPT-4o",
                type=AgentTypeEnum.system,
                provider=AgentProviderEnum.openai,
                model="gpt-4o",
                description="Optimized version of GPT-4 with improved performance",
                capabilities=["reasoning", "code", "analysis", "vision", "fast"],
                avatar_url="⚡",
                max_tokens=4096,
                temperature=0.7,
                status=AgentStatusEnum.online,
                is_active=True
            )
            session.add(gpt4o)
            
            gpt35 = Agent(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                type=AgentTypeEnum.system,
                provider=AgentProviderEnum.openai,
                model="gpt-3.5-turbo",
                description="Fast and efficient model for general tasks",
                capabilities=["general", "fast", "efficient"],
                avatar_url="💬",
                max_tokens=4096,
                temperature=0.7,
                status=AgentStatusEnum.online,
                is_active=True
            )
            session.add(gpt35)
            
            logger.info("Added OpenAI agents")
        
        # Add Ollama agents if configured
        if settings.ai.provider == "ollama":
            llama = Agent(
                id="llama3",
                name="Llama 3",
                type=AgentTypeEnum.system,
                provider=AgentProviderEnum.ollama,
                model="llama3.1:latest",
                description="Meta's Llama 3 model running locally",
                capabilities=["general", "code", "local", "private"],
                base_url=settings.ai.ollama_base_url,
                avatar_url="🦙",
                max_tokens=4096,
                temperature=0.7,
                status=AgentStatusEnum.online,
                is_active=True
            )
            session.add(llama)
            
            logger.info("Added Ollama agents")
        
        session.commit()
        logger.info("Default agents added successfully!")


def main():
    """Main migration function."""
    try:
        create_tables()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()