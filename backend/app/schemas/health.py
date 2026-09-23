"""Pydantic v2 schemas for health and readiness probes."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DependencyHealth(BaseModel):
    """Health status representation for an external system dependency."""

    model_config = ConfigDict(extra="ignore")

    configured: bool = Field(
        ...,
        description="Whether the external dependency is explicitly configured.",
    )
    status: str = Field(
        ...,
        description="Current operational status: available, unavailable, or unconfigured.",
    )


class HealthResponse(BaseModel):
    """Liveness probe confirmation schema."""

    model_config = ConfigDict(extra="ignore")

    status: str = Field(
        default="live",
        description="Liveness status of the backend service.",
        examples=["live"],
    )
    service: str = Field(
        default="verifai-backend",
        description="Microservice identifier.",
        examples=["verifai-backend"],
    )
    version: str = Field(
        ...,
        description="Semantic application release version.",
        examples=["0.1.0"],
    )
    request_id: str | None = Field(
        default=None,
        description="Correlation trace ID propagated via X-Request-ID header.",
        examples=["req_8f1b2c3d4e5f"],
    )


class ReadinessResponse(BaseModel):
    """Readiness probe evaluation schema."""

    model_config = ConfigDict(extra="ignore")

    status: str = Field(
        ...,
        description="Readiness status: ready or not_ready.",
        examples=["ready", "not_ready"],
    )
    ready: bool = Field(
        ...,
        description="Boolean readiness flag.",
        examples=[True, False],
    )
    process: str = Field(
        default="running",
        description="FastAPI ASGI worker execution state.",
        examples=["running"],
    )
    environment: str = Field(
        ...,
        description="Active environment setting (development, testing, production).",
        examples=["development"],
    )
    request_id: str | None = Field(
        default=None,
        description="Correlation trace ID.",
        examples=["req_8f1b2c3d4e5f"],
    )
    message: str = Field(
        ...,
        description="Human-readable readiness explanation.",
        examples=["All dependencies configured and operational."],
    )
    dependencies: dict[str, Any] = Field(
        ...,
        description="Detailed dependency connectivity breakdown.",
    )
