#!/usr/bin/env python3
"""
Database migration script for authentication tables.
Run this script to add user authentication tables to the existing database.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import SQLModel, create_engine, Session
from oneline_chat.core.config import Settings
from oneline_chat.db.models import User, UserSession, OnelineChat
from oneline_chat.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def create_auth_tables():
    """Create authentication tables in the database."""
    # Load settings
    settings = Settings()
    
    # Create database URL
    database_url = f"postgresql://{settings.database.user}:{settings.database.password}@{settings.database.host}:{settings.database.port}/{settings.database.name}"
    
    logger.info(f"Connecting to database: {settings.database.name} on {settings.database.host}")
    
    # Create engine
    engine = create_engine(database_url, echo=False)
    
    try:
        # Create all tables
        logger.info("Creating authentication tables...")
        SQLModel.metadata.create_all(engine)
        logger.info("✓ Authentication tables created successfully")
        
        # Verify tables exist
        with Session(engine) as session:
            # Test query to ensure tables are accessible
            session.exec(select(User).limit(1)).first()
            session.exec(select(UserSession).limit(1)).first()
            logger.info("✓ Tables verified and accessible")
            
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise
    finally:
        engine.dispose()


def add_user_id_to_existing_chats():
    """Add user_id column to existing chat records (nullable)."""
    settings = Settings()
    database_url = f"postgresql://{settings.database.user}:{settings.database.password}@{settings.database.host}:{settings.database.port}/{settings.database.name}"
    
    engine = create_engine(database_url, echo=False)
    
    try:
        with engine.connect() as conn:
            # Check if user_id column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='oneline_chat' AND column_name='user_id'
            """))
            
            if not result.fetchone():
                logger.info("Adding user_id column to oneline_chat table...")
                conn.execute(text("""
                    ALTER TABLE oneline_chat 
                    ADD COLUMN IF NOT EXISTS user_id INTEGER 
                    REFERENCES users(id) ON DELETE CASCADE
                """))
                conn.commit()
                logger.info("✓ user_id column added to oneline_chat table")
            else:
                logger.info("✓ user_id column already exists in oneline_chat table")
                
    except Exception as e:
        logger.error(f"Failed to add user_id column: {e}")
        # This is not critical - existing chats will just not have a user
        logger.warning("Existing chats will not be associated with users")
    finally:
        engine.dispose()


def main():
    """Run the migration."""
    logger.info("Starting authentication migration...")
    
    try:
        # Create authentication tables
        create_auth_tables()
        
        # Update existing tables
        add_user_id_to_existing_chats()
        
        logger.info("✅ Migration completed successfully!")
        logger.info("You can now use authentication features in your application.")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    from sqlmodel import select, text
    main()