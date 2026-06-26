from __future__ import annotations

import asyncio
import time

import pytest

from src.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


class TestCircuitBreaker:
    async def test_initial_state(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60, success_threshold=2)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    async def test_opens_after_failures(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60, success_threshold=2)

        async def fail():
            raise ValueError("fail")

        for i in range(3):
            with pytest.raises(ValueError):
                await cb.call(fail)

        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    async def test_open_raises_error(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60, success_threshold=2)

        async def fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await cb.call(fail)

        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(fail)

    async def test_half_open_after_timeout(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=1, success_threshold=2)
        cb._state_changed_at = time.time() - 2  # force recovery

        async def fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await cb.call(fail)

        assert cb.state == CircuitState.OPEN
        cb._state_changed_at = 0  # force timeout
        cb.failure_count = 1

        with pytest.raises(ValueError):
            await cb.call(fail)

    async def test_closes_after_successes(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=1, success_threshold=2)

        async def succeed():
            return "ok"

        async def fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await cb.call(fail)

        assert cb.state == CircuitState.OPEN
        cb._state_changed_at = 0

        with pytest.raises(ValueError):
            await cb.call(fail)

        cb.state = CircuitState.HALF_OPEN

        result1 = await cb.call(succeed)
        assert result1 == "ok"
        result2 = await cb.call(succeed)
        assert result2 == "ok"
        assert cb.state == CircuitState.CLOSED

    async def test_reset(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60, success_threshold=2)
        cb.failure_count = 5
        cb.state = CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    async def test_metrics(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60, success_threshold=2)
        metrics = cb.state_metrics
        assert metrics["name"] == "test"
        assert metrics["state"] == "closed"

    async def test_success_resets_failures(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60, success_threshold=2)
        cb.failure_count = 2

        async def succeed():
            return "ok"

        await cb.call(succeed)
        assert cb.failure_count == 0
