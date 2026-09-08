"""Main entry point for VerifAI backend application."""

import uvicorn
from app.core.config import get_settings
from app.factory import create_app

# Instantiate standard application for ASGI servers (e.g. Uvicorn / Gunicorn)
app = create_app()

if __name__ == "__main__":  # pragma: no cover
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # Handled by our structured logging setup
    )

