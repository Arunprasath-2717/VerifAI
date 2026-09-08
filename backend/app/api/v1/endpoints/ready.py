"""Readiness check endpoint (GET /api/v1/ready)."""

from fastapi import APIRouter, HTTPException, status
from app.core.database import database_manager
from app.schemas.common import StandardResponse
from app.schemas.health import ReadinessData

router = APIRouter()


@router.get(
    "/ready",
    response_model=StandardResponse[ReadinessData],
    summary="Readiness probe",
    description="Verifies that all essential dependencies (e.g. database) are operational to serve traffic.",
    responses={
        200: {"description": "Application is ready to handle traffic"},
        503: {"description": "Application is not ready to handle traffic"},
    },
)
async def get_readiness() -> StandardResponse[ReadinessData]:
    """Verify backend readiness to serve traffic."""
    db_healthy, db_status, _ = await database_manager.check_health()

    checks = {
        "database": "connected" if db_healthy else "disconnected",
    }

    if not db_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "type": "SERVICE_UNAVAILABLE",
                "message": "Application is not ready to serve traffic: database unavailable",
                "details": {
                    "status": "not_ready",
                    "checks": checks,
                },
            },
        )

    return StandardResponse(
        success=True,
        data=ReadinessData(
            status="ready",
            checks=checks,
        ),
    )
