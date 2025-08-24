"""
Logging configuration for Oneline Chat.
"""

import logging
import logging.config
import sys
from typing import Dict, Any, Optional


def get_logging_config(settings: Optional[Any] = None) -> Dict[str, Any]:
    """Get logging configuration based on environment."""
    
    # Allow settings to be passed in or imported
    if settings is None:
        try:
            from .config import settings
        except ImportError:
            # Fallback to basic config
            return get_basic_logging_config()
    
    log_level = settings.app.log_level.upper()
    
    if settings.app.is_production:
        # Production: JSON format for structured logging
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "format": '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s","module":"%(module)s","function":"%(funcName)s","line":%(lineno)d}',
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "json",
                    "stream": sys.stdout
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": log_level,
                    "formatter": "json",
                    "filename": "logs/oneline_chat.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "loggers": {
                "oneline_chat": {
                    "level": log_level,
                    "handlers": ["console", "file"],
                    "propagate": False
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False
                }
            },
            "root": {
                "level": log_level,
                "handlers": ["console"]
            }
        }
    else:
        # Development: Human-readable format
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "simple": {
                    "format": "%(levelname)s - %(name)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "detailed" if log_level == "DEBUG" else "simple",
                    "stream": sys.stdout
                }
            },
            "loggers": {
                "oneline_chat": {
                    "level": log_level,
                    "handlers": ["console"],
                    "propagate": False
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False
                }
            },
            "root": {
                "level": log_level,
                "handlers": ["console"]
            }
        }


def get_basic_logging_config() -> Dict[str, Any]:
    """Get basic logging configuration when settings not available."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(levelname)s - %(name)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": sys.stdout
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"]
        }
    }


def setup_logging(settings: Optional[Any] = None) -> None:
    """Setup logging configuration."""
    import os
    
    # Get settings
    if settings is None:
        try:
            from .config import settings
        except ImportError:
            settings = None
    
    # Create logs directory in production
    if settings and hasattr(settings.app, 'is_production') and settings.app.is_production:
        os.makedirs("logs", exist_ok=True)
    
    # Configure logging
    config = get_logging_config(settings)
    logging.config.dictConfig(config)
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    if settings:
        logger.info(f"Logging configured for {settings.app.environment} environment")
        logger.info(f"Log level: {settings.app.log_level}")
    else:
        logger.info("Logging configured with basic settings")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)