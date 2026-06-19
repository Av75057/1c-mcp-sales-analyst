from __future__ import annotations

from datetime import date, timedelta

from src.insights.detectors.base import BaseDetector
from src.insights.models import Priority, RawInsight
from src.logger import logger
from src.tools import get_client


class SalesGrowthDetector(BaseDetector):
    async def detect(self, tenant_id: str = "default") -> list[RawInsight]:
        logger.info("SalesGrowthDetector: запуск")
        client = get_client()
        today = date.today()
        month_ago = today - timedelta(days=30)
        two_months_ago = today - timedelta(days=60)

        current = await client.get_sales(
            date_from=month_ago.isoformat(),
            date_to=today.isoformat(),
        )
        previous = await client.get_sales(
            date_from=two_months_ago.isoformat(),
            date_to=month_ago.isoformat(),
        )

        if not current or not previous:
            return []

        curr_total = sum(s.get("quantity", 0) for s in current)
        prev_total = sum(s.get("quantity", 0) for s in previous)

        insights: list[RawInsight] = []
        if prev_total > 0:
            delta = (curr_total - prev_total) / prev_total
            if delta >= self.config.sales_growth_threshold:
                insights.append(RawInsight(
                    detector="sales_growth",
                    priority=Priority.INFO,
                    title=f"Рост продаж: +{round(delta * 100, 1)}% за неделю",
                    entity_type="total",
                    entity_id="total",
                    entity_name="Все товары",
                    metric_name="sales_volume",
                    metric_value=curr_total,
                    metric_baseline=prev_total,
                    metric_delta_percent=round(delta * 100, 1),
                    period_from=month_ago,
                    period_to=today,
                    context={"direction": "growth"},
                    tenant_id=tenant_id,
                ))

        logger.info("SalesGrowthDetector: готово")
        return insights
