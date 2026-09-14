"""Application factory module for VerifAI backend."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from fastapi import FastAPI

from app.api.health import router as root_health_router
from app.api.v1.router import api_v1_router
from app.core.config import Settings, get_settings
from app.core.database import database_manager
from app.core.errors import register_error_handlers
from app.core.logging import logger, setup_logging
from app.core.middleware import configure_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and graceful shutdown lifecycle."""
    settings: Settings = app.state.settings

    # 1. Startup phase
    setup_logging(log_level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)
    logger.info(
        "Starting %s v%s in [%s] mode...",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )

    # Initialize database pool
    await database_manager.connect(
        database_url=settings.DATABASE_URL,
        min_size=settings.DB_POOL_MIN_SIZE,
        max_size=settings.DB_POOL_MAX_SIZE,
        timeout=settings.DB_TIMEOUT,
    )

    yield

    # 2. Shutdown phase
    logger.info("Initiating graceful shutdown...")
    await database_manager.disconnect()
    logger.info("Graceful shutdown completed.")


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Application factory for VerifAI backend.

    Initializes FastAPI app, loads configuration, configures middleware,
    registers error handlers, mounts versioned routes, and enables documentation.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "VerifAI — AI Claim Verification & Trust-Scoring System Backend API. "
            "Phase 0 Foundation providing health, readiness, and metrics infrastructure."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Attach settings to application state
    app.state.settings = settings

    # Configure middleware stack
    configure_middleware(app, settings)

    # Register global exception handlers
    register_error_handlers(app)

    # Register root routes
    app.include_router(root_health_router)

    # Register API v1 routes
    app.include_router(api_v1_router, prefix="/api/v1")

    return app
