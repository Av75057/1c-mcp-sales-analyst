from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from typing import Any


class LRUCache:
    def __init__(self, max_size: int = 200, ttl: int = 300):
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl

    def _make_key(self, **kwargs: Any) -> str:
        raw = json.dumps({k: v for k, v in kwargs.items() if v is not None}, sort_keys=True, default=str)
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        expires, val = self._store.pop(key)
        if time.time() < expires:
            self._store[key] = (expires, val)
            return val
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if len(self._store) >= self._max_size:
            self._store.popitem(last=False)
        self._store[key] = (time.time() + (ttl or self._ttl), value)

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


search_cache = LRUCache(max_size=200, ttl=300)
