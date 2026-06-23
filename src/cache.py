from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from src.logger import logger


class MemoryCache:
    def __init__(self, ttl: int = 60) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        if key in self._store:
            expires, val = self._store[key]
            if time.time() < expires:
                return val
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._store[key] = (time.time() + (ttl or self._ttl), value)

    def clear(self) -> None:
        self._store.clear()


cache = MemoryCache(ttl=60)


def _make_key(prefix: str, **kwargs: Any) -> str:
    raw = json.dumps({k: v for k, v in kwargs.items() if v}, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()[:12]}"


class CachedC1Client:
    def __init__(self, client: Any, ttl: int = 30) -> None:
        self._client = client
        self._ttl = ttl

    async def get_stock(self, **kwargs: Any) -> Any:
        key = _make_key("stock", **kwargs)
        return await self._with_cache(key, self._client.get_stock, **kwargs)

    async def get_sales(self, **kwargs: Any) -> Any:
        key = _make_key("sales", **kwargs)
        return await self._with_cache(key, self._client.get_sales, **kwargs)

    async def get_sales_by_manager(self, **kwargs: Any) -> Any:
        key = _make_key("sales_by_manager", **kwargs)
        return await self._with_cache(key, self._client.get_sales_by_manager, **kwargs)

    async def get_receivables(self, **kwargs: Any) -> Any:
        key = _make_key("receivables", **kwargs)
        return await self._with_cache(key, self._client.get_receivables, **kwargs)

    async def get_purchases(self, **kwargs: Any) -> Any:
        key = _make_key("purchases", **kwargs)
        return await self._with_cache(key, self._client.get_purchases, **kwargs)

    async def list_nomenclature(self, **kwargs: Any) -> Any:
        key = _make_key("nomenclature", **kwargs)
        return await self._with_cache(key, self._client.list_nomenclature, **kwargs)

    async def get_price_history(self, **kwargs: Any) -> Any:
        key = _make_key("price_history", **kwargs)
        return await self._with_cache(key, self._client.get_price_history, **kwargs)

    async def get_purchase_orders(self, **kwargs: Any) -> Any:
        key = _make_key("purchase_orders", **kwargs)
        return await self._with_cache(key, self._client.get_purchase_orders, **kwargs)

    async def get_item_movement(self, **kwargs: Any) -> Any:
        key = _make_key("item_movement", **kwargs)
        return await self._with_cache(key, self._client.get_item_movement, **kwargs)

    async def ping(self) -> bool:
        return await self._client.ping()

    async def _with_cache(self, key: str, method: Any, **kwargs: Any) -> Any:
        cached_val = cache.get(key)
        if cached_val is not None:
            logger.debug("Cache HIT: {}", key)
            return cached_val
        result = await method(**kwargs)
        cache.set(key, result, ttl=self._ttl)
        logger.debug("Cache MISS: {}", key)
        return result
