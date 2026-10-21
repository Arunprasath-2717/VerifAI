"""FastAPI application entry point and factory for VerifAI."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import build_api_router
from app.core.config import Settings, get_settings
from app.core.database import dispose_async_engine
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.core.middleware import BodySizeLimitMiddleware, RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and shutdown events."""
    settings = get_settings()
    logger = logging.getLogger("app")

    # Startup lifecycle hook
    logger.info(
        "Starting %s v%s in '%s' environment (debug=%s)",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.ENVIRONMENT,
        settings.DEBUG,
    )
    if settings.ENABLE_LIVE_SEARCH:
        from app.modules.evidence.live_retriever import LiveWebRetriever

        tiers = LiveWebRetriever.from_settings().describe_tiers()
        logger.info("Live search tiers available: %s", tiers)
        if not any(tiers.values()):
            logger.warning("ENABLE_LIVE_SEARCH is on but no live tier is usable.")
    if not settings.demo_evidence_index_enabled and not settings.ENABLE_LIVE_SEARCH:
        logger.warning(
            "No external evidence source enabled: claims without private-KB "
            "evidence will resolve to UNKNOWN. Set ENABLE_LIVE_SEARCH=true."
        )
    if not settings.API_KEYS and not settings.is_development:
        logger.error(
            "API_KEYS is not configured: all non-health requests will be "
            "rejected with HTTP 401 in '%s'.",
            settings.ENVIRONMENT,
        )
    yield

    # Shutdown lifecycle hook: Dispose engine and pool connections cleanly
    logger.info("Initiating graceful shutdown for %s...", settings.PROJECT_NAME)
    await dispose_async_engine()
    logger.info("Database engine resources successfully disposed.")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app_settings = settings or get_settings()

    # Configure centralized structured logging idempotently
    setup_logging(log_level=app_settings.LOG_LEVEL)

    application = FastAPI(
        title=app_settings.PROJECT_NAME,
        version=app_settings.VERSION,
        description=app_settings.DESCRIPTION,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Bound request bodies before any parsing (inner to request-ID tracking so
    # rejections still carry a correlation ID).
    application.add_middleware(
        BodySizeLimitMiddleware,
        max_bytes=app_settings.MAX_REQUEST_BODY_BYTES,
        header_name=app_settings.REQUEST_ID_HEADER,
    )

    # Attach Request ID & correlation tracking middleware (runs for all requests)
    application.add_middleware(
        RequestIDMiddleware,
        header_name=app_settings.REQUEST_ID_HEADER,
    )

    # Configure CORS middleware
    if app_settings.BACKEND_CORS_ORIGINS:
        is_wildcard = "*" in app_settings.BACKEND_CORS_ORIGINS
        application.add_middleware(
            CORSMiddleware,
            allow_origins=app_settings.BACKEND_CORS_ORIGINS,
            allow_credentials=not is_wildcard,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
            allow_headers=["*"],
        )

    # Register standardized API error handlers
    register_error_handlers(
        application,
        header_name=app_settings.REQUEST_ID_HEADER,
    )

    # Mount versioned API routes exclusively under /api/v1 (no unversioned duplicates)
    application.include_router(build_api_router(app_settings.API_V1_STR))

    return application


app = create_app()
