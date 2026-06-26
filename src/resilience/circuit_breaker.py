from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from src.logger import logger


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        self._state_changed_at: float = time.time()

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    @property
    def state_metrics(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": datetime.fromtimestamp(self.last_failure_time).isoformat() if self.last_failure_time else None,
        }

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self._state_changed_at > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("[CB] {} переходит в HALF_OPEN", self.name)
            else:
                raise CircuitBreakerOpenError(f"{self.name} circuit breaker OPEN (failed {self.failure_count}/{self.failure_threshold})")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._reset("closed via HALF_OPEN")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self, error: Exception) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold and self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self._state_changed_at = time.time()
            logger.error("[CB] {} переходит в OPEN (ошибок: {}/{})", self.name, self.failure_count, self.failure_threshold)

    def _reset(self, reason: str = "") -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info("[CB] {} сброшен: {}", self.name, reason)

    def reset(self) -> None:
        self._reset("admin reset")


deepseek_cb = CircuitBreaker(name="deepseek", failure_threshold=5, recovery_timeout=60, success_threshold=2)
c1_cb = CircuitBreaker(name="c1", failure_threshold=3, recovery_timeout=30, success_threshold=2)
