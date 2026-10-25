"""Pydantic schemas for dashboard statistics and aggregate metrics."""

from pydantic import BaseModel, Field

from app.schemas.verification import VerificationResponse


class ChartPointSchema(BaseModel):
    """Single point in a timeseries chart."""

    day: str = Field(description="Formatted date label, e.g. Mon, Oct 4")
    date: str = Field(description="ISO date string YYYY-MM-DD")
    verifications: int = Field(default=0)
    claims: int = Field(default=0)
    evidence: int = Field(default=0)


class StatCardMetric(BaseModel):
    """Stat card metrics payload."""

    title: str
    value: str
    trend: str = "+0%"
    sub: str
    sparkline: list[int] = Field(default_factory=list)


class DashboardLeaderboardEntry(BaseModel):
    """Leaderboard entry for dashboard display."""

    rank: int
    model: str
    provider: str
    accuracy: float
    hallucination_rate: float
    latency_ms: int
    certified: bool = True


class DashboardStatsResponse(BaseModel):
    """Complete aggregated dashboard payload."""

    verifications_count: int = 0
    claims_count: int = 0
    evidence_sources_count: int = 0
    conversations_count: int = 0
    weekly_chart_data: list[ChartPointSchema] = Field(default_factory=list)
    monthly_chart_data: list[ChartPointSchema] = Field(default_factory=list)
    recent_verifications: list[VerificationResponse] = Field(default_factory=list)
    stat_cards: list[StatCardMetric] = Field(default_factory=list)
    leaderboard_preview: list[DashboardLeaderboardEntry] = Field(default_factory=list)
