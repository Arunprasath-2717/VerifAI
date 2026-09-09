"""API v1 router aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, metrics, ready, test_echo

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(health.router, tags=["System Health"])
api_v1_router.include_router(ready.router, tags=["Readiness"])
api_v1_router.include_router(metrics.router, tags=["Metrics"])
api_v1_router.include_router(test_echo.router, tags=["Validation Test"])

