"""Detailed system health check endpoint (GET /api/v1/health)."""

from fastapi import APIRouter, HTTPException, Request, status
from app.core.config import Settings
from app.core.database import database_manager
from app.schemas.common import StandardResponse
from app.schemas.health import SystemHealthData

router = APIRouter()


@router.get(
    "/health",
    response_model=StandardResponse[SystemHealthData],
    summary="System and dependency health check",
    description="Reports the overall health status of VerifAI including database connectivity.",
    responses={
        200: {"description": "System and database are healthy"},
        503: {"description": "One or more core components are unhealthy"},
    },
)
async def get_system_health(
    request: Request,
) -> StandardResponse[SystemHealthData]:
    """Inspect application and database health."""
    settings: Settings = getattr(request.app.state, "settings", None)
    if settings is None:
        from app.core.config import get_settings
        settings = get_settings()

    db_healthy, db_status, _ = await database_manager.check_health()

    if not db_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "type": "SERVICE_UNHEALTHY",
                "message": "System health check failed: database is disconnected",
                "details": {
                    "status": "unhealthy",
                    "version": settings.APP_VERSION,
                    "environment": settings.ENVIRONMENT,
                    "database": "disconnected",
                },
            },
        )

    return StandardResponse(
        success=True,
        data=SystemHealthData(
            status="healthy",
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
            database="connected",
        ),
    )
