"""Health and readiness check endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.config import Settings
from app.core.database import check_database_connectivity
from app.core.dependencies import get_current_settings
from app.core.logging import get_current_request_id

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
        "request_id": get_current_request_id(),
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

    # Knowledge documents and evidence are stored in the same SQL database.
    # There is no independently configured object-storage service to probe.
    storage_check = {
        "configured": db_check["configured"],
        "status": db_check["status"],
        "backend": "database",
    }

    # JWT signing/verification is local. Check its configuration, not token issuance
    # or a remote Firebase/JWKS endpoint on every Kubernetes readiness probe.
    # This is a configuration check, NOT a live identity-provider health check.
    jwt_secret = settings.JWT_SECRET.get_secret_value().strip()
    firebase_configured = not settings.FIREBASE_AUTH_ENABLED or bool(
        settings.FIREBASE_PROJECT_ID.strip()
    )
    auth_configured = bool(jwt_secret) and firebase_configured
    auth_check = {
        "configured": auth_configured,
        "status": "available" if auth_configured else "unconfigured",
        "check": "configuration_only",
    }

    dependencies = {
        "database": db_check,
        "storage": storage_check,
        "auth": auth_check,
    }

    # Readiness checks local configuration plus live database connectivity.
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
            "request_id": get_current_request_id(),
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
        "request_id": get_current_request_id(),
        "message": "All dependencies configured and operational.",
        "dependencies": dependencies,
    }
