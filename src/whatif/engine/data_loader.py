from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.clients.mock_c1_client import MockC1Client
from src.config import settings
from src.logger import logger
from src.tools import get_client


class DataLoader:
    async def get_sales_history(
        self,
        entity_type: str = "nomenclature",
        entity_name: str | None = None,
        period_months: int = 12,
    ) -> list[dict[str, Any]]:
        logger.info("DataLoader: загрузка истории продаж {} {}", entity_type, entity_name)
        client = get_client()
        today = date.today()
        date_from = today - timedelta(days=period_months * 30)

        sales = await client.get_sales(
            date_from=date_from.isoformat(),
            date_to=today.isoformat(),
        )

        if entity_name:
            sales = [s for s in sales if entity_name.lower() in s.get("nomenclature", "").lower()]

        logger.info("DataLoader: загружено {} записей", len(sales))
        return sales

    async def get_price_history(
        self,
        entity_id: str = "",
        period_months: int = 12,
    ) -> list[dict[str, Any]]:
        logger.info("DataLoader: загрузка истории цен")
        return []

    async def get_stock_data(
        self,
        entity_name: str | None = None,
    ) -> list[dict[str, Any]]:
        logger.info("DataLoader: загрузка остатков")
        client = get_client()
        stock = await client.get_stock()
        if entity_name:
            stock = [s for s in stock if entity_name.lower() in s.get("nomenclature", "").lower()]
        return stock
