"""Health and readiness response schemas."""

from typing import Dict, Literal
from pydantic import BaseModel, Field


class RootHealthData(BaseModel):
    """Payload for basic liveness endpoint (GET /health)."""

    status: str = Field(default="healthy", description="Application liveness status")


class SystemHealthData(BaseModel):
    """Payload for system health endpoint (GET /api/v1/health)."""

    status: Literal["healthy", "unhealthy", "degraded"] = Field(
        ..., description="Overall system health status"
    )
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    database: Literal["connected", "disconnected"] = Field(
        ..., description="Database connection status"
    )


class ReadinessData(BaseModel):
    """Payload for Kubernetes-style readiness endpoint (GET /api/v1/ready)."""

    status: Literal["ready", "not_ready"] = Field(
        ..., description="Readiness status to receive traffic"
    )
    checks: Dict[str, str] = Field(..., description="Status breakdown of essential dependencies")
