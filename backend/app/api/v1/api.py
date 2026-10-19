"""API v1 router composition."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    chat,
    dashboard,
    health,
    history,
    ingestion,
    knowledge,
    legal,
    models,
    providers,
    reports,
    verification,
)

api_v1_router = APIRouter()

# Core system endpoints
api_v1_router.include_router(health.router, tags=["Health & Readiness"])
api_v1_router.include_router(auth.router, tags=["Authentication & RBAC"])
api_v1_router.include_router(legal.router, tags=["Legal Compliance & Consent"])
api_v1_router.include_router(dashboard.router, tags=["Dashboard & Metrics"])
api_v1_router.include_router(chat.router, tags=["Chat & Multi-LLM"])
api_v1_router.include_router(models.router, tags=["Model Ecosystem & Discovery"])
api_v1_router.include_router(history.router, tags=["History & User Lifecycle"])
api_v1_router.include_router(verification.router, tags=["Verification"])
api_v1_router.include_router(ingestion.router, tags=["Ingestion"])
api_v1_router.include_router(knowledge.router, tags=["Knowledge Base"])
api_v1_router.include_router(reports.router, tags=["Reports & Analytics"])
api_v1_router.include_router(providers.router, tags=["AI Providers"])
