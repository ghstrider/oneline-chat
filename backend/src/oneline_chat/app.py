"""
FastAPI application for Oneline Chat.
This module exports the centralized application instance.
"""

from .core.application import app, settings

__all__ = ['app', 'settings']