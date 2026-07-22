# START_MODULE_CONTRACT: c1_http_client
# DESCRIPTION: HTTP-клиент для 1С:УНФ с Basic Auth, retry, circuit breaker
# DEPENDENCIES: httpx, src.resilience.circuit_breaker, src.observability.metrics
# CONTRACTS: docs/requirements.xml
# ERRORS: C1ClientError, C1TimeoutError, C1ConnectionError, CircuitBreakerOpenError
# END_MODULE_CONTRACT

from __future__ import annotations

import asyncio
import base64
import time
from typing import Any

import httpx

from src.config import settings
from src.logger import logger
from src.metrics import metrics
from src.observability.metrics import c1_requests_total, c1_request_duration_seconds, c1_errors_total
from src.resilience.circuit_breaker import c1_cb, CircuitBreakerOpenError


class C1ClientError(Exception):
    """Ошибка при работе с 1С HTTP API."""
    pass


class C1TimeoutError(C1ClientError):
    """Таймаут при запросе к 1С."""
    pass


class C1ConnectionError(C1ClientError):
    """Ошибка подключения к 1С."""
    pass


class C1Client:
    def __init__(self, base_url: str | None = None, username: str | None = None, password: str | None = None) -> None:
        self.base_url = (base_url or settings.c1_base_url).rstrip("/")
        user = username or settings.c1_username
        pw = password or settings.c1_password
        raw = f"{user}:{pw}".encode("utf-8")
        self._auth_header = "Basic " + base64.b64encode(raw).decode("ascii")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(
            settings.c1_timeout_seconds,
            connect=settings.c1_connect_timeout_seconds,
        )
        self._max_retries = settings.c1_max_retries
        self._retry_delay = settings.c1_retry_delay_seconds

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        endpoint = path.split("/")[-1]
        metrics.inc_active()
        start = time.perf_counter()

        if c1_cb.is_open:
            raise C1ConnectionError("1С временно недоступна. Попробуйте позже.")

        for attempt in range(self._max_retries):
            try:
                client = await self._get_client()
                resp = await client.request(method, path, **kwargs)
                elapsed = time.perf_counter() - start
                metrics.record_request(endpoint, elapsed)

                if resp.status_code >= 400:
                    try:
                        body = resp.text[:500]
                    except Exception:
                        body = "(тело нечитаемо)"
                    logger.error(
                        "[PERF] HTTP {} {} ERROR {}: {}",
                        method, path, resp.status_code, body,
                    )
                    metrics.record_error(endpoint, f"HTTP_{resp.status_code}", body)

                    if resp.status_code == 503 and attempt < self._max_retries - 1:
                        logger.warning(
                            "1С недоступен (503), retry {}/{}",
                            attempt + 1, self._max_retries,
                        )
                        await asyncio.sleep(self._retry_delay)
                        continue

                    resp.raise_for_status()

                logger.info(
                    "[PERF] HTTP {} {}: {:.3f}s status={}",
                    method, path, elapsed, resp.status_code,
                )
                if elapsed > 3.0:
                    logger.warning("[PERF] SLOW HTTP {} {}: {:.3f}s", method, path, elapsed)
                c1_cb._on_success()
                c1_requests_total.labels(endpoint=endpoint, status="ok").inc()
                c1_request_duration_seconds.labels(endpoint=endpoint).observe(elapsed)
                return resp

            except httpx.TimeoutException:
                elapsed = time.perf_counter() - start
                logger.error(
                    "[PERF] HTTP TIMEOUT {} {}: {:.3f}s attempt {}/{}",
                    method, path, elapsed, attempt + 1, self._max_retries,
                )
                metrics.record_timeout(endpoint, elapsed)
                c1_errors_total.labels(error_type="timeout", endpoint=endpoint).inc()
                if attempt == self._max_retries - 1:
                    c1_cb._on_failure(httpx.TimeoutException("1С timeout"))
                    raise C1TimeoutError(
                        f"1С не отвечает: {path} ({elapsed:.1f}s)"
                    )
                await self._client_reset()
                await asyncio.sleep(self._retry_delay)

            except httpx.ConnectError:
                elapsed = time.perf_counter() - start
                logger.error(
                    "[PERF] HTTP CONNECT ERROR {} {}: {:.3f}s attempt {}/{}",
                    method, path, elapsed, attempt + 1, self._max_retries,
                )
                c1_errors_total.labels(error_type="connect", endpoint=endpoint).inc()
                if attempt == self._max_retries - 1:
                    c1_cb._on_failure(httpx.ConnectError("1С connection failed"))
                    raise C1ConnectionError(
                        f"Не удалось подключиться к 1С: {path} ({elapsed:.1f}s)"
                    )
                await self._client_reset()
                await asyncio.sleep(self._retry_delay)

            except httpx.HTTPStatusError as e:
                elapsed = time.perf_counter() - start
                logger.error(
                    "[PERF] HTTP ERROR {} {}: {} {:.3f}s",
                    method, path, e.response.status_code, elapsed,
                )
                raise C1ClientError(
                    f"1С вернула {e.response.status_code}: {path} ({elapsed:.1f}s)"
                ) from e

            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(
                    "[PERF] HTTP UNKNOWN ERROR {} {}: {:.3f}s - {}",
                    method, path, elapsed, e,
                )
                metrics.record_error(endpoint, "unknown", str(e))
                if attempt == self._max_retries - 1:
                    raise C1ClientError(
                        f"Ошибка запроса к 1С: {path} ({elapsed:.1f}s): {e}"
                    ) from e
                await asyncio.sleep(self._retry_delay)

        else:
            metrics.dec_active()
            raise C1ClientError(f"Не удалось выполнить запрос после {self._max_retries} попыток")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            limits = httpx.Limits(max_keepalive_connections=0, max_connections=5)
            self._client = httpx.AsyncClient(
                headers={"Authorization": self._auth_header},
                timeout=self._timeout,
                limits=limits,
            )
        return self._client

    async def _client_reset(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _normalize_stock(self, data: list[dict[str, Any]], warehouse: str | None = None) -> list[dict[str, Any]]:
        return [
            {
                "nomenclature": d.get("item", d.get("nomenclature", "")),
                "warehouse": d.get("organization", d.get("warehouse", warehouse or "Неизвестно")),
                "quantity": d.get("quantity", 0),
                "unit": d.get("unit", "шт"),
            }
            for d in data
        ]

    def _normalize_sales(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "date": d.get("date", ""),
                "nomenclature": d.get("item", d.get("nomenclature", "")),
                "quantity": d.get("quantity", 0),
                "sum": d.get("sum", d.get("cost", 0)),
                "cost": d.get("Себестоимость", d.get("cost_price", d.get("cost", 0))),
                "manager": d.get("manager", ""),
                "client": d.get("client", d.get("counterparty", "")),
                "warehouse": d.get("organization", d.get("warehouse", "")),
                "document_number": d.get("document_number", ""),
            }
            for d in data
        ]

    async def get_sales_with_docs(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"limit": str(limit), "with_docs": "1"}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        logger.debug("GET /sales with_docs params={}", params)
        resp = await self._request("GET", f"{self.base_url}/sales", params=params)
        return self._normalize_sales(resp.json())

    def _normalize_sales_by_manager(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "manager": d.get("manager", ""),
                "total_sum": d.get("total_sum", d.get("sum", 0)),
                "total_quantity": d.get("total_quantity", d.get("quantity", 0)),
            }
            for d in data
        ]

    def _normalize_receivables(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "client": d.get("client", d.get("counterparty", "")),
                "amount": d.get("amount", 0),
                "overdue_days": d.get("overdue_days", d.get("days_overdue", 0)),
            }
            for d in data
        ]

    def _normalize_purchases(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "date": d.get("date", ""),
                "nomenclature": d.get("item", ""),
                "quantity": d.get("quantity", 0),
                "sum": d.get("sum", 0),
                "supplier": d.get("supplier", ""),
            }
            for d in data
        ]

    def _normalize_nomenclature(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "ref": d.get("ref", ""),
                "name": d.get("name", d.get("title", "")),
                "unit": d.get("unit", d.get("measure", "")),
                "item_type": d.get("item_type", ""),
                "article": d.get("article", d.get("code", d.get("Артикул", ""))),
                "code": d.get("code", d.get("Код", "")),
            }
            for d in data
        ]

    async def get_stock(
        self,
        warehouse: str | None = None,
        nomenclature: str | None = None,
        min_quantity: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if nomenclature:
            params["item"] = nomenclature
        if warehouse:
            params["organization"] = warehouse
        if min_quantity is not None:
            params["min_quantity"] = str(min_quantity)

        logger.debug("GET /stock params={}", params)
        resp = await self._request("GET", f"{self.base_url}/stock", params=params)
        return self._normalize_stock(resp.json(), warehouse=warehouse)

    async def get_sales(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        manager: str | None = None,
        warehouse: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"limit": str(limit)}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if manager:
            params["manager"] = manager
        if warehouse:
            params["organization"] = warehouse

        logger.debug("GET /sales params={}", params)
        resp = await self._request("GET", f"{self.base_url}/sales", params=params)
        return self._normalize_sales(resp.json())

    async def get_sales_by_manager(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        manager: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"limit": "1000"}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if manager:
            params["manager"] = manager

        logger.debug("GET /sales/by_manager params={}", params)
        resp = await self._request("GET", f"{self.base_url}/sales/by_manager", params=params)
        return self._normalize_sales_by_manager(resp.json())

    async def get_receivables(
        self,
        min_amount: float | None = None,
        date_from: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if min_amount is not None:
            params["min_amount"] = str(min_amount)
        if date_from:
            params["date_from"] = date_from

        logger.debug("GET /receivables params={}", params)
        resp = await self._request("GET", f"{self.base_url}/receivables", params=params)
        return self._normalize_receivables(resp.json())

    async def get_purchases(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        item: str | None = None,
        supplier: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if item:
            params["item"] = item
        if supplier:
            params["supplier"] = supplier

        logger.debug("GET /purchases params={}", params)
        resp = await self._request("GET", f"{self.base_url}/purchases", params=params)
        return self._normalize_purchases(resp.json())

    async def list_nomenclature(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        params = {"q": query, "limit": str(limit)}
        for method, kwargs in [("GET", {"params": params}), ("POST", {"data": params})]:
            logger.debug("{} /nomenclature/search params={}", method, params)
            try:
                resp = await self._request(method, f"{self.base_url}/nomenclature/search", **kwargs)
                data: list[dict[str, Any]] = resp.json()
                return self._normalize_nomenclature(data)
            except Exception as e:
                logger.debug("{} failed: {}", method, e)
        # Fallback: extract unique nomenclature from sales documents
        logger.warning("nomenclature/search failed, falling back to sales data")
        try:
            sales = await self.get_sales(limit=2000)
            seen = set()
            items = []
            for s in sales:
                name = s.get("nomenclature", "") or s.get("item", "")
                if name and name not in seen and (not query or query.lower() in name.lower()):
                    seen.add(name)
                    items.append({"name": name, "ref": "", "article": "", "unit": "", "item_type": ""})
            logger.info("Fallback: found {} items from sales data", len(items))
            return items[:limit]
        except Exception as e2:
            logger.error("Fallback also failed: {}", e2)
            return []

    async def get_price_history(
        self,
        item: str,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        params = {"item": item, "limit": str(limit)}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        resp = await self._request("GET", f"{self.base_url}/pricehistory", params=params)
        return resp.json()

    async def get_purchase_orders(
        self,
        item: str | None = None,
        supplier: str | None = None,
        status: str = "open",
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"status": status}
        if item:
            params["item"] = item
        if supplier:
            params["supplier"] = supplier
        resp = await self._request("GET", f"{self.base_url}/purchaseorders", params=params)
        return resp.json()

    async def get_item_movement(
        self,
        item: str,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"item": item}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        resp = await self._request("GET", f"{self.base_url}/itemmovement", params=params)
        return resp.json()

    async def ping(self) -> bool:
        try:
            resp = await self._request("GET", f"{self.base_url}/stock", params={"limit": "1"})
            return resp.status_code < 500
        except Exception:
            return False
        finally:
            metrics.dec_active()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def reset(self) -> None:
        await self.close()
        logger.info("[PERF] C1Client сброшен (пересоздание httpx клиента)")

    async def __aenter__(self) -> C1Client:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
