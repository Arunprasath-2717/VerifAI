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
    assert len(data) >= 3
    assert data[0]["rank"] == 1
    assert "categories" in data[0]
    assert "factualSupport" in data[0]["categories"]


def test_providers_endpoints(client: TestClient):
    """Confirm /api/v1/providers lists and tests providers."""
    list_resp = client.get("/api/v1/providers")
    assert list_resp.status_code == 200
    providers = list_resp.json()
    assert isinstance(providers, list)
    assert any(p["id"] == "prov-openai" for p in providers)

    # Test link key
    save_resp = client.post(
        "/api/v1/providers/prov-mistral/key",
        json={"apiKey": "mistral-secret-key-12345678"},
    )
    assert save_resp.status_code == 200
    saved = save_resp.json()
    assert saved["status"] == "Connected"
    assert "mist" in saved["keyMasked"]
    assert "mistral-secret-key-12345678" not in saved["keyMasked"]  # Key must be masked!

    # Test connection ping
    test_resp = client.post("/api/v1/providers/prov-mistral/test")
    assert test_resp.status_code == 200
    assert test_resp.json()["success"] is True

    # Test unlink key
    unlink_resp = client.delete("/api/v1/providers/prov-mistral/key")
    assert unlink_resp.status_code == 200
    assert unlink_resp.json()["unlinked"] is True
