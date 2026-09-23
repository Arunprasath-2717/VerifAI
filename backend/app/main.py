"""FastAPI application entry point and factory for VerifAI."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import dispose_async_engine
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware


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
    yield

    # Shutdown lifecycle hook: Dispose engine and pool connections cleanly
    logger.info("Initiating graceful shutdown for %s...", settings.PROJECT_NAME)
    await dispose_async_engine()
    logger.info("Database engine resources successfully disposed.")


OPENAPI_TAGS = [
    {
        "name": "Health & Readiness",
        "description": "Liveness and dependency readiness probes for zero-downtime orchestration.",
    },
    {
        "name": "Verification",
        "description": (
            "End-to-end claim extraction, evidence retrieval, multi-judge evaluation, "
            "and consensus verdict generation."
        ),
    },
    {
        "name": "Ingestion",
        "description": (
            "SSRF-protected payload ingestion for browser extensions, webhooks, "
            "and client integrations."
        ),
    },
    {
        "name": "Knowledge Base",
        "description": (
            "Namespace-isolated private document management, text chunking, and "
            "deterministic evidence retrieval."
        ),
    },
]


def create_app(settings: Settings | None = None) -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app_settings = settings or get_settings()

    # Configure centralized structured logging idempotently
    setup_logging(log_level=app_settings.LOG_LEVEL)

    application = FastAPI(
        title=app_settings.PROJECT_NAME,
        version=app_settings.VERSION,
        description=app_settings.DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        contact={
            "name": "VerifAI Team",
            "url": "https://github.com/Arunprasath-2717/VerifAI",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "docExpansion": "list",
            "defaultModelsExpandDepth": 2,
        },
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
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
    application.include_router(api_router)

    return application


app = create_app()
