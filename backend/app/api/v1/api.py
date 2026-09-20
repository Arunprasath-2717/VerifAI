"""API v1 router composition."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, verification

api_v1_router = APIRouter()

# Core system endpoints
api_v1_router.include_router(health.router, tags=["Health & Readiness"])
api_v1_router.include_router(verification.router, tags=["Verification"])
