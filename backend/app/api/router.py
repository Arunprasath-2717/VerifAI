"""Top-level API router for VerifAI."""

from fastapi import APIRouter

from app.api.v1.api import api_v1_router


def build_api_router(api_v1_prefix: str) -> APIRouter:
    """Compose versioned routers under the configured prefix.

    Built per application so ``create_app(settings)`` honours its own
    ``API_V1_STR`` instead of whatever settings existed at import time.
    """
    router = APIRouter()
    router.include_router(api_v1_router, prefix=api_v1_prefix)
    return router
