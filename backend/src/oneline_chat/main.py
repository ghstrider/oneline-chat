"""
Main entry point for Oneline Chat application.
"""

import uvicorn
from .core.application import application


def main():
    """Main entry point for the application."""
    settings = application.get_settings()
    
    # Start the application
    uvicorn.run(
        "oneline_chat.app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.reload and settings.app.is_development,
        log_level=settings.app.log_level.lower()
    )


if __name__ == "__main__":
    main()