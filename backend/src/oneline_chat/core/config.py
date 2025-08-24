"""
Core configuration settings for Oneline Chat.
"""

import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")
    name: str = Field(default="oneline_chat_app", env="DB_NAME")
    
    @property
    def url(self) -> str:
        """Get database URL."""
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.name}"
    
    @property
    def test_url(self) -> str:
        """Get test database URL."""
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/test_db"
        return f"postgresql://{self.user}@{self.host}:{self.port}/test_db"


class AISettings(BaseSettings):
    """AI provider configuration."""
    
    provider: Literal["openai", "ollama"] = Field(default="ollama", env="AI_PROVIDER")
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Ollama settings
    ollama_base_url: str = Field(default="http://localhost:11434/v1", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="deepseek-r1:8b", env="OLLAMA_MODEL")
    ollama_api_key: str = Field(default="ollama", env="OLLAMA_API_KEY")
    
    @property
    def default_model(self) -> str:
        """Get default model based on provider."""
        if self.provider == "ollama":
            return self.ollama_model
        return "gpt-3.5-turbo"


class AppSettings(BaseSettings):
    """Application configuration."""
    
    title: str = "Oneline Chat API"
    version: str = "0.1.0"
    description: str = "OpenAI-compatible streaming chat API with PostgreSQL persistence"
    
    host: str = Field(default="0.0.0.0", env="APP_HOST")
    port: int = Field(default=8000, env="APP_PORT")
    reload: bool = Field(default=True, env="APP_RELOAD")
    
    environment: Literal["development", "staging", "production"] = Field(
        default="development", env="APP_ENV"
    )
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS settings
    cors_origins: list[str] = Field(
        default=["*"], env="CORS_ORIGINS"
    )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


class Settings(BaseSettings):
    """Main settings class combining all configurations."""
    
    app: AppSettings = AppSettings()
    database: DatabaseSettings = DatabaseSettings()
    ai: AISettings = AISettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()