"""Root liveness endpoint (GET /health)."""

from fastapi import APIRouter
from app.schemas.common import StandardResponse
from app.schemas.health import RootHealthData

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=StandardResponse[RootHealthData],
    summary="Basic application liveness check",
    description="Lightweight, unauthenticated liveness probe indicating the HTTP process is running.",
)
async def root_health_check() -> StandardResponse[RootHealthData]:
    """Return basic liveness status."""
    return StandardResponse(
        success=True,
        data=RootHealthData(status="healthy"),
    )
