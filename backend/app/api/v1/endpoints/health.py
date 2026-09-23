"""Health and readiness check endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.config import Settings
from app.core.database import check_database_connectivity
from app.core.dependencies import get_current_settings
from app.core.logging import get_current_request_id
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get(
    "/health",
    summary="Liveness Check",
    description="Confirms that the FastAPI application is alive and responsive.",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
async def get_health(
    settings: Settings = Depends(get_current_settings),
) -> HealthResponse:
    """Return process liveness confirmation."""
    return HealthResponse(
        status="live",
        service="verifai-backend",
        version=settings.VERSION,
        request_id=get_current_request_id(),
    )


@router.get(
    "/ready",
    summary="Readiness Probe",
    description=(
        "Evaluates whether the application is ready to accept and process traffic. "
        "Returns HTTP 503 when critical dependencies are unconfigured or unavailable."
    ),
    response_model=ReadinessResponse,
    responses={
        200: {"description": "All required dependencies operational and ready."},
        503: {"description": "Critical dependencies unconfigured or unavailable."},
    },
)
async def get_ready(
    response: Response,
    settings: Settings = Depends(get_current_settings),
) -> ReadinessResponse:
    """Evaluate application readiness and dependency availability.

    Queries database connectivity dynamically without leaking secrets, connection URLs,
    or raw database exceptions.
    """
    db_check = await check_database_connectivity(settings=settings)

    dependencies = {
        "database": db_check,
        "storage": {
            "configured": False,
            "status": "unconfigured",
        },
        "auth": {
            "configured": False,
            "status": "unconfigured",
        },
    }

    # All critical dependencies must be configured and available for readiness
    is_ready = all(
        dep.get("configured") is True and dep.get("status") == "available"
        for dep in dependencies.values()
    )

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="not_ready",
            ready=False,
            process="running",
            environment=settings.ENVIRONMENT,
            request_id=get_current_request_id(),
            message=(
                "Application process is alive, but critical dependencies are "
                "unconfigured or unavailable."
            ),
            dependencies=dependencies,
        )

    return ReadinessResponse(
        status="ready",
        ready=True,
        process="running",
        environment=settings.ENVIRONMENT,
        request_id=get_current_request_id(),
        message="All dependencies configured and operational.",
        dependencies=dependencies,
    )
