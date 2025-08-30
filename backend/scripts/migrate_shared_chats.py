#!/usr/bin/env python3
"""
Migration script to add shared_chats table for chat sharing functionality.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from sqlmodel import create_engine, text
from oneline_chat.core.config import settings

def main():
    print("🔄 Creating shared_chats table for chat sharing functionality...")
    
    try:
        engine = create_engine(settings.database.url)
        
        with engine.connect() as conn:
            print("Creating shared_chats table...")
            
            # Create the shared_chats table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS shared_chats (
                    id SERIAL PRIMARY KEY,
                    share_token VARCHAR(64) UNIQUE NOT NULL,
                    chat_id VARCHAR NOT NULL,
                    owner_id VARCHAR NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description VARCHAR(500),
                    is_public BOOLEAN DEFAULT TRUE NOT NULL,
                    expires_at TIMESTAMP,
                    view_count INTEGER DEFAULT 0 NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            
            # Create indexes for better performance
            print("Creating indexes...")
            
            # Index on share_token for fast lookups
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shared_chats_share_token 
                ON shared_chats(share_token)
            """))
            
            # Index on chat_id and owner_id for ownership checks
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shared_chats_chat_owner 
                ON shared_chats(chat_id, owner_id)
            """))
            
            # Index on is_public and expires_at for public access
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shared_chats_public_access 
                ON shared_chats(is_public, expires_at)
            """))
            
            conn.commit()
            print("✅ shared_chats table and indexes created successfully")
        
        return 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())