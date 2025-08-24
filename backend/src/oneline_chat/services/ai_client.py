"""
AI Client configuration for OpenAI and Ollama support.
"""

from openai import AsyncOpenAI

from ..core.logging import get_logger

logger = get_logger(__name__)

# Global client instance
client = None


def get_ai_client() -> AsyncOpenAI:
    """
    Get configured AI client based on AI provider settings.
    
    Returns:
        AsyncOpenAI: Configured client for either OpenAI or Ollama
    """
    global client
    from ..core.config import settings
    
    if settings.ai.provider == "ollama":
        logger.info(f"Initializing Ollama client: {settings.ai.ollama_base_url}")
        
        client = AsyncOpenAI(
            base_url=settings.ai.ollama_base_url,
            api_key=settings.ai.ollama_api_key,
        )
        return client
    
    elif settings.ai.provider == "openai":
        if not settings.ai.openai_api_key:
            logger.warning("OpenAI API key not configured properly")
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        logger.info("Initializing OpenAI client")
        
        client = AsyncOpenAI(api_key=settings.ai.openai_api_key)
        return client
    
    else:
        raise ValueError(f"Unsupported AI_PROVIDER: {settings.ai.provider}. Use 'openai' or 'ollama'")


def get_default_model() -> str:
    """
    Get default model name based on AI provider.
    
    Returns:
        str: Default model name
    """
    from ..core.config import settings
    return settings.ai.default_model


def get_ai_provider() -> str:
    """
    Get current AI provider.
    
    Returns:
        str: Current AI provider ('openai' or 'ollama')
    """
    from ..core.config import settings
    return settings.ai.provider


def is_ollama_provider() -> bool:
    """
    Check if current provider is Ollama.
    
    Returns:
        bool: True if using Ollama, False otherwise
    """
    from ..core.config import settings
    return settings.ai.provider == "ollama"


def is_openai_provider() -> bool:
    """
    Check if current provider is OpenAI.
    
    Returns:
        bool: True if using OpenAI, False otherwise
    """
    from ..core.config import settings
    return settings.ai.provider == "openai"


# Initialize client on module load
client = get_ai_client()