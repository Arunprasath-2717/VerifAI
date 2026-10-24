"""Tests for dashboard, reports, models leaderboard, and providers endpoints."""

import pytest
from starlette.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_dashboard_stats_endpoint(client: TestClient):
    """Confirm /api/v1/dashboard/stats returns real aggregate schema."""
    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "verifications_count" in data
    assert "claims_count" in data
    assert "evidence_sources_count" in data
    assert "conversations_count" in data
    assert "weekly_chart_data" in data
    assert "monthly_chart_data" in data
    assert "stat_cards" in data
    assert len(data["stat_cards"]) == 4


def test_reports_analytics_endpoint(client: TestClient):
    """Confirm /api/v1/reports/analytics computes data for requested timeframe."""
    resp = client.get("/api/v1/reports/analytics?timeframe=30D")
    assert resp.status_code == 200
    data = resp.json()
    assert data["timeframe"] == "30D"
    assert "chart_data" in data
    assert "model_usage" in data
    assert "evidence_sources" in data
    assert "supported_rate" in data


def test_models_leaderboard_endpoint(client: TestClient):
    """Confirm /api/v1/models/leaderboard returns ranked frontier models."""
    resp = client.get("/api/v1/models/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # No fabricated benchmark observations may be returned when none are stored.
    assert data == []


def test_providers_endpoints_require_authentication(client: TestClient):
    """Provider routes are owner-scoped; anonymous callers are rejected.

    Full BYOK behavior (save, persist, test, unlink, isolation) is covered in
    test_provider_credentials.py against the isolated test database.
    """
    assert client.get("/api/v1/providers").status_code == 401
    assert (
        client.post(
            "/api/v1/providers/prov-mistral/key", json={"apiKey": "x" * 12}
        ).status_code
        == 401
    )
    assert client.post("/api/v1/providers/prov-mistral/test").status_code == 401
    assert client.delete("/api/v1/providers/prov-mistral/key").status_code == 401
