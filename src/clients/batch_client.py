# START_MODULE_CONTRACT: batch_client
# DESCRIPTION: Batch-клиент для группировки запросов к 1С в один HTTP-вызов
# DEPENDENCIES: httpx, src.clients.c1_client
# CONTRACTS: docs/requirements.xml#get_analytics_context
# FALLBACK: sequential через C1Client при 404/timeout
# END_MODULE_CONTRACT

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from src.config import settings
from src.logger import logger
from src.metrics import metrics


class BatchC1Client:
    """Batch-клиент для группировки запросов к 1С.

    Позволяет выполнить несколько запросов к 1С в одном HTTP-вызове
    через эндпоинт POST /api/v1/batch.
    """

    def __init__(self) -> None:
        self.base_url = settings.c1_base_url.rstrip("/")
        raw = f"{settings.c1_username}:{settings.c1_password}".encode("utf-8")
        import base64
        self._auth_header = "Basic " + base64.b64encode(raw).decode("ascii")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(
            settings.c1_batch_timeout_seconds,
            connect=settings.c1_connect_timeout_seconds,
        )
        self._batch_url = self.base_url.replace("/hs/api", "/hs/api/v1") + "/batch"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            limits = httpx.Limits(max_keepalive_connections=0, max_connections=5)
            self._client = httpx.AsyncClient(
                headers={"Authorization": self._auth_header},
                timeout=self._timeout,
                limits=limits,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> BatchC1Client:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def execute_batch(
        self,
        requests: list[dict[str, Any]],
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Выполняет batch-запрос к 1С.

        Args:
            requests: Список запросов вида:
                [{"id": "...", "method": "GET", "path": "...", "params": {...}}, ...]
            timeout: Таймаут в секундах (переопределяет настройку по умолчанию)

        Returns:
            {"results": [...], "total_execution_time_ms": ...}
        """
        client = await self._get_client()
        payload = {"requests": requests}
        timeout_val = timeout or settings.c1_batch_timeout_seconds

        logger.info(
            "[BATCH] Отправка {} запросов в batch (timeout={}s)",
            len(requests), timeout_val,
        )

        start = time.perf_counter()
        try:
            resp = await client.post(
                self._batch_url,
                json=payload,
                timeout=timeout_val,
            )
            elapsed = time.perf_counter() - start

            if resp.status_code == 404:
                logger.warning("[BATCH] Batch-эндпоинт не найден (404), использую fallback")
                return await self._fallback_sequential(requests)

            if resp.status_code >= 400:
                body = resp.text[:500]
                logger.error("[BATCH] Ошибка {}: {}", resp.status_code, body)
                logger.warning("[BATCH] Batch недоступен, использую fallback")
                return await self._fallback_sequential(requests)

            result: dict[str, Any] = resp.json()
            total_time = result.get("total_execution_time_ms", 0)
            logger.info(
                "[BATCH] Выполнено {} запросов за {:.3f}s (1С: {}ms)",
                len(requests), elapsed, total_time,
            )
            metrics.record_request("batch", elapsed)
            return result

        except (httpx.TimeoutException, httpx.ConnectError):
            elapsed = time.perf_counter() - start
            logger.error(
                "[BATCH] Таймаут/ошибка подключения batch ({:.3f}s), fallback", elapsed,
            )
            metrics.record_timeout("batch", elapsed)
            return await self._fallback_sequential(requests)

    async def _fallback_sequential(
        self,
        requests: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Fallback: выполняет запросы последовательно через отдельные HTTP-вызовы."""
        logger.info("[BATCH] Fallback: последовательное выполнение {} запросов", len(requests))
        from src.clients.c1_client import C1Client

        results: list[dict[str, Any]] = []
        total_ms = 0

        async with C1Client() as c1:
            for req in requests:
                req_start = time.perf_counter()
                try:
                    method = req.get("method", "GET").lower()
                    path = req.get("path", "")
                    params = req.get("params", {})

                    if method == "get":
                        http_method = "GET"
                    elif method == "post":
                        http_method = "POST"
                    else:
                        http_method = "GET"

                    resp = await c1._request(
                        http_method,
                        f"{c1.base_url}{path}",
                        params=params if http_method == "GET" else None,
                        json=params if http_method == "POST" else None,
                    )
                    data = resp.json()
                    elapsed_ms = (time.perf_counter() - req_start) * 1000
                    results.append({
                        "id": req.get("id", ""),
                        "status": resp.status_code,
                        "data": data,
                        "execution_time_ms": round(elapsed_ms, 2),
                    })
                    total_ms += elapsed_ms

                except Exception as e:
                    elapsed_ms = (time.perf_counter() - req_start) * 1000
                    logger.error("[BATCH] Fallback ошибка {}: {}", req.get("id"), e)
                    results.append({
                        "id": req.get("id", ""),
                        "status": 500,
                        "error": str(e),
                        "execution_time_ms": round(elapsed_ms, 2),
                    })
                    total_ms += elapsed_ms

        return {
            "results": results,
            "total_execution_time_ms": round(total_ms, 2),
        }

    async def get_analytics_context(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """Получает полный контекст для AI-аналитики одним batch-запросом.

        Returns:
            {
                "sales_summary": {...},
                "top_products": [...],
                "top_customers": [...],
                "inventory": {...},
                "slow_moving": [...],
                "execution_time_ms": ...
            }
        """
        params: dict[str, str] = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        requests = [
            {"id": "sales", "method": "GET", "path": "/sales", "params": {**params, "limit": "20"}},
            {"id": "sales_by_manager", "method": "GET", "path": "/sales/by_manager", "params": params},
            {"id": "stock", "method": "GET", "path": "/stock", "params": {"limit": "10"}},
        ]

        batch_result = await self.execute_batch(requests)

        context: dict[str, Any] = {
            "execution_time_ms": batch_result.get("total_execution_time_ms", 0),
        }

        for r in batch_result.get("results", []):
            rid = r.get("id", "")
            if r.get("status") == 200:
                context[rid] = r.get("data")
            else:
                logger.warning("[BATCH] Запрос {} вернул ошибку: {}", rid, r.get("error", "неизвестно"))
                context[rid] = {"error": r.get("error", "Ошибка запроса")}

        return context

    async def get_sales_summary(self, date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
        result = await self.get_analytics_context(date_from=date_from, date_to=date_to)
        return {"sales": result.get("sales", []), "sales_by_manager": result.get("sales_by_manager", [])}

    async def get_top_products(self, date_from: str | None = None, date_to: str | None = None, limit: int = 20) -> list[Any]:
        result = await self.get_analytics_context(date_from=date_from, date_to=date_to)
        sales = result.get("sales", [])
        return sorted(sales, key=lambda x: x.get("sum", 0), reverse=True)[:limit]

    async def get_top_customers(self, date_from: str | None = None, date_to: str | None = None, limit: int = 10) -> list[Any]:
        result = await self.get_analytics_context(date_from=date_from, date_to=date_to)
        all_sales = result.get("sales", [])
        customers: dict[str, float] = {}
        for s in all_sales:
            c = s.get("client", "")
            customers[c] = customers.get(c, 0) + s.get("sum", 0)
        sorted_c = sorted(customers.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"customer": k, "total_sales": v} for k, v in sorted_c]
