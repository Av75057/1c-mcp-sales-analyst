from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable

from src.logger import logger


def measure_time(name: str | None = None, slow_threshold: float = 3.0) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            label = name or func.__name__
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.info("[PERF] {}: {:.3f}s", label, elapsed)
                if elapsed > slow_threshold:
                    logger.warning("[PERF] SLOW {}: {:.3f}s", label, elapsed)
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error("[PERF] {} FAILED: {:.3f}s - {}", label, elapsed, e)
                raise
        return wrapper
    return decorator
