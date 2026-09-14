"""Tests for Kubernetes-style readiness probe (GET /api/v1/ready)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ready_endpoint_ready(client: AsyncClient, mock_db_connected):
    """Verify readiness returns 200 when database is operational."""
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ready"
    assert body["data"]["checks"]["database"] == "connected"


@pytest.mark.asyncio
async def test_ready_endpoint_not_ready(client: AsyncClient, mock_db_disconnected):
    """Verify readiness returns 503 when database is unavailable."""
    response = await client.get("/api/v1/ready")
    assert response.status_code == 503
    assert "application/json" in response.headers["content-type"]

    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "SERVICE_UNAVAILABLE"
    assert body["error"]["details"]["status"] == "not_ready"
    assert body["error"]["details"]["checks"]["database"] == "disconnected"
