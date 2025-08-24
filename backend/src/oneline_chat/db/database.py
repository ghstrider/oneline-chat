"""
Database connection and session management for Oneline Chat.
"""

from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import text
from typing import Generator

from ..core.logging import get_logger

logger = get_logger(__name__)


def get_engine():
    """Get database engine with application settings."""
    from ..core.config import settings
    return create_engine(
        settings.database.url,
        echo=settings.app.is_development,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )

engine = get_engine()


def create_db_and_tables() -> None:
    """Create database schema and tables."""
    try:
        # Create all tables
        SQLModel.metadata.create_all(engine)
        logger.info("All database tables created successfully")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
            logger.info(f"Tables in database: {tables}")
            
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_session() -> Generator[Session, None, None]:
    """Get database session for dependency injection."""
    with Session(engine) as session:
        yield session