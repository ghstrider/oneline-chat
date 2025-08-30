#!/usr/bin/env python3
"""
Database migration script for chat history features.
Adds metadata fields to support chat history management.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlmodel import SQLModel, create_engine, Session, select, text
from oneline_chat.core.config import Settings
from oneline_chat.db.models import OnelineChat
from oneline_chat.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def add_chat_metadata_fields():
    """Add chat metadata fields to existing oneline_chat table."""
    settings = Settings()
    database_url = f"postgresql://{settings.database.user}:{settings.database.password}@{settings.database.host}:{settings.database.port}/{settings.database.name}"
    
    logger.info(f"Connecting to database: {settings.database.name} on {settings.database.host}")
    
    engine = create_engine(database_url, echo=False)
    
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='oneline_chat' 
                AND column_name IN ('chat_title', 'created_at', 'updated_at', 'is_deleted')
            """))
            
            existing_columns = {row[0] for row in result.fetchall()}
            logger.info(f"Existing columns: {existing_columns}")
            
            # Add missing columns
            migrations = []
            
            if 'chat_title' not in existing_columns:
                migrations.append("""
                    ALTER TABLE oneline_chat 
                    ADD COLUMN chat_title VARCHAR(255) DEFAULT NULL
                """)
                logger.info("Will add chat_title column")
            
            if 'created_at' not in existing_columns:
                migrations.append("""
                    ALTER TABLE oneline_chat 
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
                logger.info("Will add created_at column")
            
            if 'updated_at' not in existing_columns:
                migrations.append("""
                    ALTER TABLE oneline_chat 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
                logger.info("Will add updated_at column")
                
            if 'is_deleted' not in existing_columns:
                migrations.append("""
                    ALTER TABLE oneline_chat 
                    ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE
                """)
                logger.info("Will add is_deleted column")
            
            # Execute migrations
            for migration in migrations:
                logger.info(f"Executing: {migration.strip()}")
                conn.execute(text(migration))
            
            if migrations:
                conn.commit()
                logger.info(f"✓ Added {len(migrations)} new columns to oneline_chat table")
            else:
                logger.info("✓ All columns already exist in oneline_chat table")
                
    except Exception as e:
        logger.error(f"Failed to add chat metadata columns: {e}")
        raise
    finally:
        engine.dispose()


def populate_existing_data():
    """Populate metadata for existing chat records."""
    settings = Settings()
    database_url = f"postgresql://{settings.database.user}:{settings.database.password}@{settings.database.host}:{settings.database.port}/{settings.database.name}"
    
    engine = create_engine(database_url, echo=False)
    
    try:
        with Session(engine) as session:
            # Update created_at and updated_at for existing records that have NULL values
            logger.info("Updating timestamps for existing chat records...")
            
            # Set created_at and updated_at to msg_timestamp for existing records
            session.execute(text("""
                UPDATE oneline_chat 
                SET created_at = msg_timestamp, 
                    updated_at = msg_timestamp 
                WHERE created_at IS NULL OR updated_at IS NULL
            """))
            
            # Generate chat titles for existing chats based on first message
            logger.info("Generating chat titles for existing chats...")
            
            session.execute(text("""
                UPDATE oneline_chat 
                SET chat_title = CASE 
                    WHEN LENGTH(question) > 50 
                    THEN SUBSTRING(question FROM 1 FOR 47) || '...'
                    ELSE question
                END
                WHERE chat_title IS NULL 
                AND question IS NOT NULL 
                AND question != ''
            """))
            
            session.commit()
            logger.info("✓ Updated existing chat records with metadata")
            
    except Exception as e:
        logger.error(f"Failed to populate existing data: {e}")
        raise
    finally:
        engine.dispose()


def create_indexes():
    """Create indexes for better query performance."""
    settings = Settings()
    database_url = f"postgresql://{settings.database.user}:{settings.database.password}@{settings.database.host}:{settings.database.port}/{settings.database.name}"
    
    engine = create_engine(database_url, echo=False)
    
    try:
        with engine.connect() as conn:
            logger.info("Creating indexes for chat history queries...")
            
            # Index for user chat queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_oneline_chat_user_updated 
                ON oneline_chat(user_id, updated_at DESC) 
                WHERE is_deleted = FALSE
            """))
            
            # Index for chat_id queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_oneline_chat_chat_id_updated 
                ON oneline_chat(chat_id, updated_at DESC) 
                WHERE is_deleted = FALSE
            """))
            
            # Index for soft delete queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_oneline_chat_deleted 
                ON oneline_chat(is_deleted)
            """))
            
            conn.commit()
            logger.info("✓ Created performance indexes")
            
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise
    finally:
        engine.dispose()


def main():
    """Run the chat history migration."""
    logger.info("Starting chat history migration...")
    
    try:
        # Add new columns
        add_chat_metadata_fields()
        
        # Populate existing data
        populate_existing_data()
        
        # Create performance indexes
        create_indexes()
        
        logger.info("✅ Chat history migration completed successfully!")
        logger.info("You can now use chat history features in your application.")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()