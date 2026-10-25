"""Prevent fabricated metrics in empty VerifAI accounts.

The session below never queries a real database or external service.
"""

import asyncio

from app.api.v1.endpoints.dashboard import get_dashboard_stats
from app.api.v1.endpoints.models import get_model_leaderboard
from app.api.v1.endpoints.reports import get_reports_analytics
from app.core.config import Settings


class EmptyResult:
    def scalar_one(self):
        return 0

    def one(self):
        return (0, 0, 0, 0, 0, 0)

    def scalars(self):
        return self

    def all(self):
        return []


class EmptyDatabase:
    async def execute(self, _query):
        return EmptyResult()


def test_empty_reports_contain_no_made_up_benchmarks():
    reports = asyncio.run(
        get_reports_analytics(
            timeframe="7D",
            current_user=None,
            db=EmptyDatabase(),
            settings=Settings(ENVIRONMENT="testing"),
        )
    )
    assert reports.total_verifications == 0
    assert reports.total_claims == 0
    assert reports.average_trust_score == 0
    assert reports.supported_rate == 0
    assert reports.contradicted_rate == 0
    assert reports.unknown_rate == 0
    assert reports.model_usage == []
    assert reports.evidence_sources == []
    assert all(point.evidence == 0 for point in reports.chart_data)


def test_empty_dashboard_does_not_invent_rankings():
    dashboard = asyncio.run(
        get_dashboard_stats(
            current_user=None,
            db=EmptyDatabase(),
            settings=Settings(ENVIRONMENT="testing"),
        )
    )
    assert dashboard.verifications_count == 0
    assert dashboard.leaderboard_preview == []
    assert all(point.verifications == 0 for point in dashboard.weekly_chart_data)


def test_leaderboard_requires_real_benchmark_records():
    assert asyncio.run(get_model_leaderboard()) == []
