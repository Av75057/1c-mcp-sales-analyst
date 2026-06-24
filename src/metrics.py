from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any


class MetricsCollector:
    """Сбор метрик производительности для MCP-сервера."""

    def __init__(self, window_seconds: int = 3600, slow_threshold: float = 3.0):
        self._window = window_seconds
        self._slow_threshold = slow_threshold
        self._response_times: deque[float] = deque(maxlen=10000)
        self._errors: deque[dict[str, Any]] = deque(maxlen=1000)
        self._timeouts: deque[dict[str, Any]] = deque(maxlen=1000)
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._active_requests: int = 0
        self._slow_queries: deque[dict[str, Any]] = deque(maxlen=100)
        self._endpoint_times: dict[str, list[float]] = defaultdict(list)

    def record_request(self, endpoint: str, elapsed: float) -> None:
        self._response_times.append(elapsed)
        self._endpoint_times[endpoint].append(elapsed)
        if elapsed > self._slow_threshold:
            self._slow_queries.append({
                "endpoint": endpoint,
                "elapsed": round(elapsed, 3),
                "timestamp": time.time(),
            })

    def record_error(self, endpoint: str, error_type: str, details: str) -> None:
        self._errors.append({
            "endpoint": endpoint,
            "error_type": error_type,
            "details": details,
            "timestamp": time.time(),
        })

    def record_timeout(self, endpoint: str, elapsed: float) -> None:
        self._timeouts.append({
            "endpoint": endpoint,
            "elapsed": round(elapsed, 3),
            "timestamp": time.time(),
        })

    def record_cache_hit(self) -> None:
        self._cache_hits += 1

    def record_cache_miss(self) -> None:
        self._cache_misses += 1

    def inc_active(self) -> None:
        self._active_requests += 1

    def dec_active(self) -> None:
        self._active_requests = max(0, self._active_requests - 1)

    def get_avg_response_time(self) -> float:
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times)

    def get_p95_response_time(self) -> float:
        if not self._response_times:
            return 0.0
        sorted_times = sorted(self._response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    def get_timeout_count(self, hours: int = 1) -> int:
        cutoff = time.time() - hours * 3600
        return sum(1 for t in self._timeouts if t["timestamp"] > cutoff)

    def get_error_count(self, hours: int = 1) -> int:
        cutoff = time.time() - hours * 3600
        return sum(1 for e in self._errors if e["timestamp"] > cutoff)

    def get_cache_hit_rate(self) -> float:
        total = self._cache_hits + self._cache_misses
        if total == 0:
            return 0.0
        return self._cache_hits / total

    def get_active_requests_count(self) -> int:
        return self._active_requests

    def get_slow_queries(self, limit: int = 10) -> list[dict[str, Any]]:
        return list(self._slow_queries)[-limit:]

    def get_endpoint_stats(self) -> dict[str, dict[str, float]]:
        stats = {}
        for endpoint, times in self._endpoint_times.items():
            if times:
                sorted_t = sorted(times)
                stats[endpoint] = {
                    "avg": round(sum(times) / len(times), 3),
                    "p95": round(sorted_t[int(len(times) * 0.95)], 3),
                    "count": len(times),
                    "max": round(max(times), 3),
                }
        return stats

    def get_summary(self) -> dict[str, Any]:
        return {
            "avg_response_time_ms": round(self.get_avg_response_time() * 1000, 2),
            "p95_response_time_ms": round(self.get_p95_response_time() * 1000, 2),
            "timeout_count_last_hour": self.get_timeout_count(hours=1),
            "error_count_last_hour": self.get_error_count(hours=1),
            "cache_hit_rate_percent": round(self.get_cache_hit_rate() * 100, 1),
            "active_requests": self.get_active_requests_count(),
            "total_requests": len(self._response_times),
            "endpoint_stats": self.get_endpoint_stats(),
        }


metrics = MetricsCollector()
