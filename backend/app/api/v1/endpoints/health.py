"""Health and readiness check endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.config import Settings
from app.core.database import check_database_connectivity
from app.core.dependencies import get_current_settings

router = APIRouter()


@router.get(
    "/health",
    summary="Liveness Check",
    description="Confirms that the FastAPI application is alive and responsive.",
    response_model=dict[str, Any],
)
async def get_health(
    settings: Settings = Depends(get_current_settings),
) -> dict[str, Any]:
    """Return process liveness confirmation."""
    return {
        "status": "live",
        "service": "verifai-backend",
        "version": settings.VERSION,
    }


@router.get(
    "/ready",
    summary="Readiness Probe",
    description=(
        "Evaluates whether the application is ready to accept and process traffic. "
        "Returns HTTP 503 when critical dependencies are unconfigured or unavailable."
    ),
    response_model=dict[str, Any],
    responses={
        200: {"description": "All required dependencies operational and ready."},
        503: {"description": "Critical dependencies unconfigured or unavailable."},
    },
)
async def get_ready(
    response: Response,
    settings: Settings = Depends(get_current_settings),
) -> dict[str, Any]:
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
        return {
            "status": "not_ready",
            "ready": False,
            "process": "running",
            "environment": settings.ENVIRONMENT,
            "message": (
                "Application process is alive, but critical dependencies are "
                "unconfigured or unavailable."
            ),
            "dependencies": dependencies,
        }

    return {
        "status": "ready",
        "ready": True,
        "process": "running",
        "environment": settings.ENVIRONMENT,
        "message": "All dependencies configured and operational.",
        "dependencies": dependencies,
    }
