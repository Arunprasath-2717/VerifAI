"""In-process metrics response schemas."""

from typing import Dict
from pydantic import BaseModel, Field


class TimingMetrics(BaseModel):
    """Response latency metrics in milliseconds."""

    average: float = Field(..., description="Average response latency in ms")
    min: float = Field(..., description="Minimum response latency in ms")
    max: float = Field(..., description="Maximum response latency in ms")
    p50: float = Field(..., description="50th percentile response latency in ms")
    p95: float = Field(..., description="95th percentile response latency in ms")


class MetricsData(BaseModel):
    """In-process application-level metrics snapshot."""

    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    total_requests: int = Field(..., description="Total HTTP requests handled")
    total_errors: int = Field(..., description="Total error responses (status >= 400)")
    active_requests: int = Field(..., description="Currently in-flight requests")
    error_rate_percentage: float = Field(..., description="Percentage of requests resulting in error")
    response_timing_ms: TimingMetrics = Field(..., description="Response latency distribution")
    requests_by_method: Dict[str, int] = Field(..., description="Request counts by HTTP method")
    requests_by_status: Dict[str, int] = Field(..., description="Request counts by HTTP status code")
    requests_by_endpoint: Dict[str, int] = Field(..., description="Request counts by normalized endpoint")
