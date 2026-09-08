"""Performance test verifying p95 latency is below 200ms."""

import time
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_and_ready_p95_latency(client: AsyncClient, mock_db_connected):
    """Verify p95 response latency for /health, /api/v1/health, and /api/v1/ready is < 200ms."""
    endpoints = ["/health", "/api/v1/health", "/api/v1/ready"]
    iterations = 100

    for endpoint in endpoints:
        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            response = await client.get(endpoint)
            duration_ms = (time.perf_counter() - start) * 1000
            assert response.status_code == 200
            latencies.append(duration_ms)

        sorted_latencies = sorted(latencies)
        p95_index = int(iterations * 0.95)
        p95_latency = sorted_latencies[p95_index]
        avg_latency = sum(latencies) / iterations

        print(
            f"\n[PERFORMANCE] {endpoint}: "
            f"avg={avg_latency:.2f}ms, p50={sorted_latencies[50]:.2f}ms, p95={p95_latency:.2f}ms"
        )

        assert p95_latency < 200.0, (
            f"Performance benchmark failed for {endpoint}: p95 latency {p95_latency:.2f}ms >= 200ms"
        )
