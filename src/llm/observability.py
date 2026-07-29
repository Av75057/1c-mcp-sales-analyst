"""LLM Observability - structured logs + metrics."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .models import LLMRequest, LLMResponse, TaskType

logger = logging.getLogger("llm.trace")


@dataclass
class LLMTrace:
    request_id: str
    session_id: str | None
    user_id: str | None
    task: str
    model: str
    provider: str
    prompt_version: str = "inline"
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    tool_calls: list[str] = field(default_factory=list)
    cached: bool = False
    error: str | None = None
    fallback_used: bool = False
    timestamp: float = field(default_factory=time.time)

    def log(self) -> None:
        level = logging.ERROR if self.error else logging.INFO
        logger.log(
            level,
            "llm_call | task=%s model=%s provider=%s "
            "tokens=%d/%d cost=$%.4f latency=%.0fms "
            "cached=%s fallback=%s error=%s",
            self.task, self.model, self.provider,
            self.tokens_in, self.tokens_out, self.cost, self.latency_ms,
            self.cached, self.fallback_used, self.error or "-",
            extra={
                "request_id": self.request_id,
                "session_id": self.session_id,
                "user_id": self.user_id,
                "task": self.task,
                "model": self.model,
                "provider": self.provider,
                "tokens_in": self.tokens_in,
                "tokens_out": self.tokens_out,
                "cost": self.cost,
                "latency_ms": self.latency_ms,
                "cached": self.cached,
                "fallback_used": self.fallback_used,
                "error": self.error,
            },
        )


class LLMMetrics:
    def __init__(self) -> None:
        self._calls: int = 0
        self._errors: int = 0
        self._total_cost: float = 0.0
        self._total_tokens_in: int = 0
        self._total_tokens_out: int = 0
        self._latencies: list[float] = []
        self._by_task: dict[str, int] = defaultdict(int)
        self._by_model: dict[str, int] = defaultdict(int)
        self._cache_hits: int = 0

    def record(self, trace: LLMTrace) -> None:
        self._calls += 1
        self._total_cost += trace.cost
        self._total_tokens_in += trace.tokens_in
        self._total_tokens_out += trace.tokens_out
        self._latencies.append(trace.latency_ms)
        self._by_task[trace.task] += 1
        self._by_model[trace.model] += 1
        if trace.cached:
            self._cache_hits += 1
        if trace.error:
            self._errors += 1

    def snapshot(self) -> dict[str, Any]:
        latencies = sorted(self._latencies) if self._latencies else [0]
        return {
            "total_calls": self._calls,
            "total_errors": self._errors,
            "error_rate": self._errors / max(self._calls, 1),
            "total_cost": round(self._total_cost, 4),
            "total_tokens_in": self._total_tokens_in,
            "total_tokens_out": self._total_tokens_out,
            "cache_hit_rate": self._cache_hits / max(self._calls, 1),
            "latency_p50": latencies[len(latencies) // 2],
            "latency_p95": latencies[int(len(latencies) * 0.95)],
            "latency_p99": latencies[int(len(latencies) * 0.99)],
            "by_task": dict(self._by_task),
            "by_model": dict(self._by_model),
        }


metrics = LLMMetrics()
