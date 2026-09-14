"""Tests for root and system health endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health_check(client: AsyncClient):
    """Verify root GET /health endpoint returns 200 and standard payload."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_system_health_healthy(client: AsyncClient, mock_db_connected):
    """Verify GET /api/v1/health returns 200 when database is connected."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
    assert body["data"]["database"] == "connected"
    assert body["data"]["version"] == "0.1.0-test"
    assert body["data"]["environment"] == "testing"


@pytest.mark.asyncio
async def test_system_health_unhealthy(client: AsyncClient, mock_db_disconnected):
    """Verify GET /api/v1/health returns 503 when database is disconnected."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 503
    assert "application/json" in response.headers["content-type"]

    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "SERVICE_UNHEALTHY"
    assert "database" in body["error"]["message"].lower()
    assert body["error"]["details"]["database"] == "disconnected"
    assert body["error"]["details"]["status"] == "unhealthy"
