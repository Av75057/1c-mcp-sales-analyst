from __future__ import annotations

from typing import Any

from src.metrics import metrics


class MetricsService:
    def get_dashboard(self) -> dict[str, Any]:
        summary = metrics.get_summary()
        return {
            "avg_response_time_ms": summary["avg_response_time_ms"],
            "p95_response_time_ms": summary["p95_response_time_ms"],
            "cache_hit_rate_percent": summary["cache_hit_rate_percent"],
            "error_count_last_hour": summary["error_count_last_hour"],
            "timeout_count_last_hour": summary["timeout_count_last_hour"],
            "active_requests": summary["active_requests"],
            "total_requests": summary["total_requests"],
        }

    def get_alerts(self) -> list[dict[str, Any]]:
        summary = metrics.get_summary()
        alerts = []
        if summary.get("avg_response_time_ms", 0) > 5000:
            alerts.append({"level": "critical", "message": f"Среднее время отклика > 5 сек: {summary['avg_response_time_ms']:.0f} мс"})
        if summary.get("timeout_count_last_hour", 0) > 10:
            alerts.append({"level": "warning", "message": f"Более 10 таймаутов за час: {summary['timeout_count_last_hour']}"})
        if summary.get("cache_hit_rate_percent", 100) < 30:
            alerts.append({"level": "info", "message": f"Cache hit rate < 30%: {summary['cache_hit_rate_percent']}%"})
        return alerts

    def get_slow_queries(self, limit: int = 10) -> list[dict[str, Any]]:
        return metrics.get_slow_queries(limit=limit)

    def get_endpoint_stats(self) -> dict[str, Any]:
        return metrics.get_endpoint_stats()
