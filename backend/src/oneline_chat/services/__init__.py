"""External services and integrations."""

from .ai_client import (
    get_ai_client,
    get_default_model,
    get_ai_provider,
    is_ollama_provider,
    is_openai_provider,
    client,
)

__all__ = [
    "get_ai_client",
    "get_default_model", 
    "get_ai_provider",
    "is_ollama_provider",
    "is_openai_provider",
    "client",
]