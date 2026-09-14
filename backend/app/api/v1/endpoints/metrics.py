"""In-process operational metrics endpoint (GET /api/v1/metrics)."""

from fastapi import APIRouter
from app.core.metrics import metrics_collector
from app.schemas.common import StandardResponse
from app.schemas.metrics import MetricsData

router = APIRouter()


@router.get(
    "/metrics",
    response_model=StandardResponse[MetricsData],
    summary="In-process operational metrics",
    description=(
        "Returns application-level in-process performance and operational metrics. "
        "Intended for student MVP monitoring without external infrastructure."
    ),
)
async def get_operational_metrics() -> StandardResponse[MetricsData]:
    """Retrieve snapshot of in-process application metrics."""
    metrics_snapshot = metrics_collector.get_metrics()
    return StandardResponse(
        success=True,
        data=MetricsData(**metrics_snapshot),
        meta={"type": "in_process_metrics", "scope": "application"},
    )
