from __future__ import annotations

from typing import Any

import httpx

from src.config import settings
from src.logger import logger


class C1ClientError(Exception):
    """Ошибка при работе с 1С HTTP API."""
    pass


class C1Client:
    def __init__(self) -> None:
        self.base_url = settings.c1_base_url.rstrip("/")
        self.auth = (settings.c1_username, settings.c1_password)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                auth=self.auth,
                timeout=30.0,
            )
        return self._client

    async def get_stock(
        self,
        warehouse: str | None = None,
        nomenclature: str | None = None,
        min_quantity: int | None = None,
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        params: dict[str, str] = {}
        # 1C expects "item" and "organization", but also accept "nomenclature"/"warehouse"
        if nomenclature:
            params["item"] = nomenclature
        if warehouse:
            params["organization"] = warehouse
        if min_quantity is not None:
            params["min_quantity"] = str(min_quantity)

        logger.debug("GET /stock params={}", params)
        resp = await client.get(f"{self.base_url}/stock", params=params)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return [
            {
                "nomenclature": d.get("item", d.get("nomenclature", "")),
                "warehouse": d.get("organization", d.get("warehouse", warehouse or "Неизвестно")),
                "quantity": d.get("quantity", 0),
                "unit": d.get("unit", "шт"),
            }
            for d in data
        ]

    async def get_sales(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        manager: str | None = None,
        warehouse: str | None = None,
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        params: dict[str, str] = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if manager:
            params["manager"] = manager
        if warehouse:
            params["organization"] = warehouse

        logger.debug("GET /sales params={}", params)
        resp = await client.get(f"{self.base_url}/sales", params=params)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return [
            {
                "date": d.get("date", ""),
                "nomenclature": d.get("item", d.get("nomenclature", "")),
                "quantity": d.get("quantity", 0),
                "sum": d.get("sum", d.get("cost", 0)),
                "manager": d.get("manager", ""),
                "client": d.get("client", d.get("counterparty", "")),
                "warehouse": d.get("organization", d.get("warehouse", "")),
            }
            for d in data
        ]

    async def get_sales_by_manager(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        manager: str | None = None,
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        params: dict[str, str] = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if manager:
            params["manager"] = manager

        logger.debug("GET /sales/by_manager params={}", params)
        resp = await client.get(f"{self.base_url}/sales/by_manager", params=params)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return [
            {
                "manager": d.get("manager", ""),
                "total_sum": d.get("total_sum", d.get("sum", 0)),
                "total_quantity": d.get("total_quantity", d.get("quantity", 0)),
            }
            for d in data
        ]

    async def get_receivables(
        self,
        min_amount: float | None = None,
        date_from: str | None = None,
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        params: dict[str, str] = {}
        if min_amount is not None:
            params["min_amount"] = str(min_amount)
        if date_from:
            params["date_from"] = date_from

        logger.debug("GET /receivables params={}", params)
        resp = await client.get(f"{self.base_url}/receivables", params=params)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return [
            {
                "client": d.get("client", d.get("counterparty", "")),
                "amount": d.get("amount", 0),
                "overdue_days": d.get("overdue_days", d.get("days_overdue", 0)),
            }
            for d in data
        ]

    async def get_purchases(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        item: str | None = None,
        supplier: str | None = None,
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
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
        resp = await client.get(f"{self.base_url}/purchases", params=params)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
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

    async def list_nomenclature(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        params = {"q": query, "limit": str(limit)}

        logger.debug("GET /nomenclature/search params={}", params)
        resp = await client.get(f"{self.base_url}/nomenclature/search", params=params)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()

        if not data and any(ord(c) > 127 for c in query):
            logger.warning(
                "Поиск номенклатуры по кириллице '{}' вернул 0 результатов. "
                "Возможно, HTTP-сервис 1С не декодирует UTF-8 параметры. "
                "Попробуйте поискать по части названия латиницей или цифрами.",
                query,
            )

        service_units = {"ч", "мес", "услуга", "раб"}
        return [
            {
                "ref": d.get("ref", ""),
                "name": d.get("name", d.get("title", "")),
                "unit": d.get("unit", d.get("measure", "")),
                "item_type": d.get("item_type", ""),
            }
            for d in data
        ]

    async def get_price_history(
        self,
        item: str,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        params = {"item": item, "limit": str(limit)}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        resp = await client.get(f"{self.base_url}/price-history", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_purchase_orders(
        self,
        item: str | None = None,
        supplier: str | None = None,
        status: str = "open",
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        params: dict[str, str] = {"status": status}
        if item:
            params["item"] = item
        if supplier:
            params["supplier"] = supplier
        resp = await client.get(f"{self.base_url}/purchase-orders", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_item_movement(
        self,
        item: str,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        params: dict[str, str] = {"item": item}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        resp = await client.get(f"{self.base_url}/item-movement", params=params)
        resp.raise_for_status()
        return resp.json()

    async def ping(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.base_url}/stock", timeout=5.0)
            return resp.status_code < 500
        except Exception:
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
