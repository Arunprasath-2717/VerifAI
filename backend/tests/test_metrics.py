"""Tests for in-process operational metrics collection and endpoint."""

import pytest
from httpx import AsyncClient
from app.core.metrics import MetricsCollector, metrics_collector


@pytest.mark.asyncio
async def test_metrics_endpoint_structure(client: AsyncClient):
    """Verify GET /api/v1/metrics returns 200 with standard schema."""
    response = await client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    body = response.json()
    assert body["success"] is True
    assert "data" in body
    data = body["data"]

    assert "uptime_seconds" in data
    assert "total_requests" in data
    assert "total_errors" in data
    assert "active_requests" in data
    assert "error_rate_percentage" in data
    assert "response_timing_ms" in data
    assert "requests_by_method" in data
    assert "requests_by_status" in data
    assert "requests_by_endpoint" in data


@pytest.mark.asyncio
async def test_metrics_increment_on_requests(client: AsyncClient, mock_db_connected):
    """Verify that requests increment total_requests, methods, and status counters."""
    # Send some requests
    await client.get("/health")
    await client.get("/api/v1/health")
    await client.get("/api/v1/nonexistent")  # 404 error

    metrics_res = await client.get("/api/v1/metrics")
    data = metrics_res.json()["data"]

    # At least 3 requests completed before /api/v1/metrics was invoked
    assert data["total_requests"] >= 3
    assert data["total_errors"] >= 1  # 404 counts as error
    assert data["requests_by_method"].get("GET", 0) >= 3
    assert data["requests_by_status"].get("404", 0) >= 1
    assert data["requests_by_status"].get("200", 0) >= 2


def test_metrics_collector_unit_calculations():
    """Unit tests for latency percentiles and boundary conditions in MetricsCollector."""
    collector = MetricsCollector(max_latency_history=5)
    collector.reset()

    # Empty metrics
    empty_stats = collector.get_metrics()
    assert empty_stats["total_requests"] == 0
    assert empty_stats["response_timing_ms"]["average"] == 0.0

    # Record 5 requests with distinct latencies
    for lat in [10.0, 20.0, 30.0, 40.0, 50.0]:
        collector.record_request_start()
        collector.record_request_end("GET", "/test", 200, lat)

    stats = collector.get_metrics()
    assert stats["total_requests"] == 5
    assert stats["total_errors"] == 0
    assert stats["error_rate_percentage"] == 0.0
    assert stats["response_timing_ms"]["min"] == 10.0
    assert stats["response_timing_ms"]["max"] == 50.0
    assert stats["response_timing_ms"]["average"] == 30.0
    assert stats["response_timing_ms"]["p50"] == 30.0
    assert stats["response_timing_ms"]["p95"] == 50.0

    # Add error request and test history capping
    collector.record_request_start()
    collector.record_request_end("POST", "/fail", 500, 100.0)
    err_stats = collector.get_metrics()
    assert err_stats["total_errors"] == 1
    assert err_stats["error_rate_percentage"] > 0
    # Latencies list capped at 5 items
    assert len(collector._latencies_ms) == 5
