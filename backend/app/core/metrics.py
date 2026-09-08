"""In-process operational metrics collector for Phase 0."""

import threading
import time
from typing import Any, Dict, List


class MetricsCollector:
    """Lightweight, thread-safe in-process metrics collector.

    NOTE: These are application-level in-process metrics intended for student MVP
    monitoring without introducing external infrastructure (Prometheus/Grafana).
    """

    def __init__(self, max_latency_history: int = 2000):
        self._lock = threading.Lock()
        self._max_history = max_latency_history
        self._start_time = time.time()

        self._total_requests: int = 0
        self._total_errors: int = 0
        self._active_requests: int = 0
        self._requests_by_method: Dict[str, int] = {}
        self._requests_by_status: Dict[str, int] = {}
        self._requests_by_endpoint: Dict[str, int] = {}
        self._latencies_ms: List[float] = []

    def record_request_start(self) -> None:
        """Track beginning of in-flight request."""
        with self._lock:
            self._active_requests += 1

    def record_request_end(
        self, method: str, endpoint: str, status_code: int, duration_ms: float
    ) -> None:
        """Track completed request metrics."""
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
            self._total_requests += 1

            if status_code >= 400:
                self._total_errors += 1

            method_key = method.upper()
            self._requests_by_method[method_key] = self._requests_by_method.get(method_key, 0) + 1

            status_key = str(status_code)
            self._requests_by_status[status_key] = self._requests_by_status.get(status_key, 0) + 1

            # Normalize endpoint to avoid infinite keys
            ep_key = endpoint.split("?")[0]
            self._requests_by_endpoint[ep_key] = self._requests_by_endpoint.get(ep_key, 0) + 1

            self._latencies_ms.append(duration_ms)
            if len(self._latencies_ms) > self._max_history:
                self._latencies_ms.pop(0)

    def get_metrics(self) -> Dict[str, Any]:
        """Compute and return a snapshot of in-process metrics."""
        with self._lock:
            uptime = round(time.time() - self._start_time, 2)
            total = self._total_requests
            errors = self._total_errors
            error_rate = round((errors / total * 100), 2) if total > 0 else 0.0

            if self._latencies_ms:
                sorted_lats = sorted(self._latencies_ms)
                count = len(sorted_lats)
                avg_lat = round(sum(sorted_lats) / count, 2)
                min_lat = round(sorted_lats[0], 2)
                max_lat = round(sorted_lats[-1], 2)
                p50_lat = round(sorted_lats[int(count * 0.50)], 2)
                p95_index = min(int(count * 0.95), count - 1)
                p95_lat = round(sorted_lats[p95_index], 2)
            else:
                avg_lat = min_lat = max_lat = p50_lat = p95_lat = 0.0

            return {
                "uptime_seconds": uptime,
                "total_requests": total,
                "total_errors": errors,
                "active_requests": self._active_requests,
                "error_rate_percentage": error_rate,
                "response_timing_ms": {
                    "average": avg_lat,
                    "min": min_lat,
                    "max": max_lat,
                    "p50": p50_lat,
                    "p95": p95_lat,
                },
                "requests_by_method": dict(self._requests_by_method),
                "requests_by_status": dict(self._requests_by_status),
                "requests_by_endpoint": dict(self._requests_by_endpoint),
            }

    def reset(self) -> None:
        """Reset metrics (useful for testing)."""
        with self._lock:
            self._start_time = time.time()
            self._total_requests = 0
            self._total_errors = 0
            self._active_requests = 0
            self._requests_by_method.clear()
            self._requests_by_status.clear()
            self._requests_by_endpoint.clear()
            self._latencies_ms.clear()


# Global singleton instance
metrics_collector = MetricsCollector()
