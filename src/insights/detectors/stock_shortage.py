from __future__ import annotations

from datetime import date, timedelta

from src.insights.detectors.base import BaseDetector
from src.insights.models import Priority, RawInsight
from src.logger import logger
from src.tools import get_client


class StockShortageDetector(BaseDetector):
    async def detect(self, tenant_id: str = "default") -> list[RawInsight]:
        logger.info("StockShortageDetector: запуск")
        client = get_client()
        today = date.today()
        month_ago = today - timedelta(days=30)

        stock = await client.get_stock()
        sales = await client.get_sales(
            date_from=month_ago.isoformat(),
            date_to=today.isoformat(),
        )

        if not stock:
            return []

        daily_sales: dict[str, float] = {}
        for s in sales:
            name = s.get("nomenclature", "")
            qty = s.get("quantity", 0)
            daily_sales[name] = daily_sales.get(name, 0) + qty / 30.0

        insights: list[RawInsight] = []
        for item in stock:
            name = item.get("nomenclature", "")
            qty = item.get("quantity", 0)
            avg_daily = daily_sales.get(name, 0)
            if avg_daily <= 0:
                continue
            days_left = qty / avg_daily
            if days_left < self.config.stock_days_threshold:
                priority = Priority.CRITICAL if days_left < 2 else Priority.WARNING
                insights.append(RawInsight(
                    detector="stock_shortage",
                    priority=priority,
                    title=f"Товар заканчивается: {name}",
                    entity_type="nomenclature",
                    entity_id=name,
                    entity_name=name,
                    metric_name="stock_days",
                    metric_value=round(days_left, 1),
                    metric_baseline=self.config.stock_days_threshold,
                    metric_delta_percent=round((days_left / self.config.stock_days_threshold - 1) * 100, 1),
                    period_from=month_ago,
                    period_to=today,
                    context={
                        "current_stock": qty,
                        "avg_daily_sales": round(avg_daily, 1),
                        "days_left": round(days_left, 1),
                    },
                    tenant_id=tenant_id,
                ))

        logger.info("StockShortageDetector: найдено {} проблем", len(insights))
        return insights
