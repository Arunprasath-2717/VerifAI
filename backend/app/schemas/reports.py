"""Schemas for reports and analytics endpoints."""

from typing import Any
from pydantic import BaseModel, Field

from app.schemas.dashboard import ChartPointSchema


class ModelUsageItem(BaseModel):
    """Model usage breakdown item."""

    model: str
    usage: int


class EvidenceSourceDomainItem(BaseModel):
    """Evidence source distribution item."""

    domain: str
    count: int


class ReportsAnalyticsResponse(BaseModel):
    """Consolidated analytics response for ReportsPage."""

    timeframe: str = "30D"
    chart_data: list[ChartPointSchema] = Field(default_factory=list)
    model_usage: list[ModelUsageItem] = Field(default_factory=list)
    evidence_sources: list[EvidenceSourceDomainItem] = Field(default_factory=list)
    total_verifications: int = 0
    total_claims: int = 0
    average_trust_score: float = 0.0
    supported_rate: float = 0.0
    contradicted_rate: float = 0.0
    unknown_rate: float = 0.0
