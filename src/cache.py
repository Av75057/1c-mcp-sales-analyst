from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import httpx

from src.logger import logger
from src.metrics import metrics


class C1UnavailableError(Exception):
    """1С HTTP API недоступна (таймаут или ошибка соединения)."""


class MemoryCache:
    def __init__(self, ttl: int = 60, max_size: int = 1000) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        if key in self._store:
            expires, val = self._store[key]
            if time.time() < expires:
                return val
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if len(self._store) >= self._max_size:
            self._store.clear()
        self._store[key] = (time.time() + (ttl or self._ttl), value)

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


cache = MemoryCache(ttl=60)


def _make_key(prefix: str, **kwargs: Any) -> str:
    raw = json.dumps({k: v for k, v in kwargs.items() if v}, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()[:12]}"


class CachedC1Client:
    def __init__(self, client: Any, ttl: int = 30) -> None:
        self._client = client
        self._ttl = ttl

    @property
    def base_url(self) -> str:
        return self._client.base_url

    @property
    def _conn_id(self) -> str | None:
        return getattr(self._client, '_conn_id', None)
    
    @_conn_id.setter
    def _conn_id(self, value: str) -> None:
        self._client._conn_id = value

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

    async def close(self) -> None:
        await self._client.close()

    async def _with_cache(self, key: str, method: Any, **kwargs: Any) -> Any:
        cached_val = cache.get(key)
        if cached_val is not None:
            result_size = len(json.dumps(cached_val, default=str))
            logger.info("[PERF] Cache HIT: {} size={}b", key, result_size)
            metrics.record_cache_hit()
            return cached_val

        metrics.record_cache_miss()
        start = time.perf_counter()
        try:
            result = await method(**kwargs)
            elapsed = time.perf_counter() - start
            result_size = len(json.dumps(result, default=str))
            logger.info(
                "[PERF] 1С {}: {:.3f}s size={}b OK",
                key, elapsed, result_size,
            )
            if elapsed > 3.0:
                logger.warning("[PERF] SLOW 1С: {} {:.3f}s", key, elapsed)
            cache.set(key, result, ttl=self._ttl)
            return result
        except C1UnavailableError:
            raise
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error("[PERF] 1С ERROR: {} {:.3f}s - {}", key, elapsed, e)
            await self._client.reset()
            raise C1UnavailableError(f"Ошибка 1С: {key} — {e}") from e
