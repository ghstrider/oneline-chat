"""
Centralized FastAPI application instance with configuration.
This module provides the single source of truth for the application instance and configuration.
"""

from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from datetime import datetime

from .config import Settings
from .logging import setup_logging, get_logger


class Application:
    """Singleton application instance with centralized configuration."""
    
    _instance: Optional['Application'] = None
    _app: Optional[FastAPI] = None
    settings: Optional[Settings] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Application, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize application only once."""
        if self._app is None:
            self._initialize()
    
    def _initialize(self):
        """Initialize configuration and create FastAPI app."""
        # Load configuration from environment first
        self._load_configuration()
        
        # Setup logging based on configuration
        setup_logging()
        self.logger = get_logger(__name__)
        
        # Create FastAPI app with lifespan events
        self._app = self._create_app()
        
        self.logger.info(f"Application initialized: {self.settings.app.title}")
        self.logger.info(f"Environment: {self.settings.app.environment}")
        self.logger.info(f"Database: {self.settings.database.name} on {self.settings.database.host}")
    
    def _load_configuration(self):
        """Load configuration from environment variables."""
        import os
        # Force reload of environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
        except ImportError:
            pass  # dotenv is optional
        
        # Create settings instance
        self.settings = Settings()
        
        # Log configuration source (after logger is initialized)
        if os.path.exists('.env'):
            pass  # Will log after logger is initialized
        else:
            pass  # Will log after logger is initialized
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Manage application lifecycle."""
        # Startup
        self.logger.info("Starting application...")
        
        # Initialize database
        await self._initialize_database()
        
        # Register startup tasks
        await self._on_startup()
        
        yield
        
        # Shutdown
        self.logger.info("Shutting down application...")
        await self._on_shutdown()
    
    async def _initialize_database(self):
        """Initialize database on startup."""
        try:
            from ..db import create_db_and_tables
            self.logger.info("Initializing database schema and tables...")
            create_db_and_tables()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            if self.settings.app.is_production:
                raise
    
    async def _on_startup(self):
        """Execute startup tasks."""
        # Initialize agent registry
        try:
            from ..api.agent_router import initialize_agents
            await initialize_agents()
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
        
        self.logger.info(f"Server ready on {self.settings.app.host}:{self.settings.app.port}")
    
    async def _on_shutdown(self):
        """Execute shutdown tasks."""
        self.logger.info("Application shutdown complete")
    
    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title=self.settings.app.title,
            description=self.settings.app.description,
            version=self.settings.app.version,
            docs_url="/docs",
            redoc_url="/redoc",
            lifespan=self.lifespan
        )
        
        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.app.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes(app)
        
        return app
    
    def _register_routes(self, app: FastAPI):
        """Register all application routes."""
        from ..api import chat_router
        from ..api.auth_router import router as auth_router
        from ..api.agent_router import router as agent_router
        
        # Include routers
        app.include_router(auth_router)
        app.include_router(chat_router)
        app.include_router(agent_router)
        
        # Root endpoint
        @app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": self.settings.app.title,
                "version": self.settings.app.version,
                "docs": "/docs",
                "endpoints": {
                    "auth": {
                        "register": "/api/v1/auth/register",
                        "login": "/api/v1/auth/login",
                        "logout": "/api/v1/auth/logout",
                        "profile": "/api/v1/auth/me"
                    },
                    "chat": {
                        "completion": "/api/v1/chat/completions",
                        "stream": "/api/v1/chat/stream",
                        "history": "/api/v1/chat/history/{chat_id}",
                        "models": "/api/v1/models"
                    },
                    "agents": {
                        "list": "/api/agents",
                        "details": "/api/agents/{agent_id}",
                        "status": "/api/agents/{agent_id}/status",
                        "select": "/api/agents/{agent_id}/select",
                        "default": "/api/agents/default"
                    }
                }
            }
        
        # Health check endpoint
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "environment": self.settings.app.environment,
                "database": "connected",
                "ai_provider": self.settings.ai.provider
            }
    
    @property
    def app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        if self._app is None:
            raise RuntimeError("Application not initialized")
        return self._app
    
    def get_settings(self) -> Settings:
        """Get application settings."""
        if self.settings is None:
            raise RuntimeError("Settings not initialized")
        return self.settings


# Global application instance
application = Application()

# Export for convenience
app = application.app
settings = application.get_settings()