#!/usr/bin/env python3
"""
Migration script to change user_id column type to support both integers and strings.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from sqlmodel import create_engine, text
from oneline_chat.core.config import settings

def main():
    print("🔄 Updating user_id column to support both integers and strings...")
    
    try:
        engine = create_engine(settings.database.url)
        
        with engine.connect() as conn:
            print("Changing user_id column type to VARCHAR...")
            
            # Remove foreign key constraint first
            conn.execute(text("""
                ALTER TABLE oneline_chat 
                DROP CONSTRAINT IF EXISTS oneline_chat_user_id_fkey
            """))
            
            # Change column type to VARCHAR
            conn.execute(text("""
                ALTER TABLE oneline_chat 
                ALTER COLUMN user_id TYPE VARCHAR USING user_id::text
            """))
            
            conn.commit()
            print("✅ user_id column updated to support both integers and strings")
        
        return 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())