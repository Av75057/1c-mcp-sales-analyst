from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any


class DrillDownCache:
    """LRU cache for drill-down results. TTL: 5 minutes."""

    def __init__(self, maxsize: int = 128, ttl: int = 300):
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl

    def _make_key(self, domain: str, parent_level: str, parent_value: str,
                  child_level: str, date_from: str, date_to: str) -> str:
        return f"{domain}:{parent_level}:{parent_value}:{child_level}:{date_from}:{date_to}"

    def get(self, domain: str, parent_level: str, parent_value: str,
            child_level: str, date_from: str, date_to: str) -> Any | None:
        key = self._make_key(domain, parent_level, parent_value, child_level, date_from, date_to)
        if key not in self._cache:
            return None
        ts, value = self._cache[key]
        if time.time() - ts > self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return value

    def set(self, domain: str, parent_level: str, parent_value: str,
            child_level: str, date_from: str, date_to: str, value: Any) -> None:
        key = self._make_key(domain, parent_level, parent_value, child_level, date_from, date_to)
        self._cache[key] = (time.time(), value)
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def invalidate(self, domain: str | None = None) -> None:
        if domain is None:
            self._cache.clear()
        else:
            self._cache = OrderedDict(
                (k, v) for k, v in self._cache.items() if not k.startswith(f"{domain}:")
            )


drilldown_cache = DrillDownCache()
