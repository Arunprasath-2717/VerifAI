"""API v1 router aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, metrics, ready, test_echo, verification

api_v1_router = APIRouter()

# Authentication & Verification (Phase 1 & 2)
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(
    verification.router, prefix="/verification", tags=["Verification"]
)

# Durga's Analytics (Phase 3)
from app.api.v1 import dashboard, leaderboard, benchmark_analytics
api_v1_router.include_router(dashboard.router)
api_v1_router.include_router(leaderboard.router)
api_v1_router.include_router(benchmark_analytics.router)

# Daranya's Modules (Phase 3)
from app.api.v1.endpoints import history, audit, provenance, reports
api_v1_router.include_router(history.router, prefix="/history", tags=["History"])
api_v1_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_v1_router.include_router(provenance.router, prefix="/claims", tags=["Provenance"])
api_v1_router.include_router(reports.router, prefix="/reports", tags=["Reports"])

# System Endpoints
api_v1_router.include_router(health.router, tags=["System Health"])
api_v1_router.include_router(ready.router, tags=["Readiness"])
api_v1_router.include_router(metrics.router, tags=["Metrics"])
api_v1_router.include_router(test_echo.router, tags=["Validation Test"])
