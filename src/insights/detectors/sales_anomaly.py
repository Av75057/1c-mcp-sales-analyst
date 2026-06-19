from __future__ import annotations

from datetime import date, timedelta

from src.clients.c1_client import C1Client
from src.insights.detectors.base import BaseDetector
from src.insights.models import Priority, RawInsight
from src.logger import logger


class SalesAnomalyDetector(BaseDetector):
    async def detect(self, tenant_id: str = "default") -> list[RawInsight]:
        logger.info("SalesAnomalyDetector: запуск")
        client = C1Client()
        today = date.today()
        # Используем месяц вместо недели, т.к. данные могут быть не за каждую неделю
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
            logger.info("SalesAnomalyDetector: недостаточно данных")
            return []

        current_by_item: dict[str, float] = {}
        for s in current:
            name = s.get("nomenclature", "")
            qty = s.get("quantity", 0)
            current_by_item[name] = current_by_item.get(name, 0) + qty

        previous_by_item: dict[str, float] = {}
        for s in previous:
            name = s.get("nomenclature", "")
            qty = s.get("quantity", 0)
            previous_by_item[name] = previous_by_item.get(name, 0) + qty

        insights: list[RawInsight] = []
        for name, prev_qty in previous_by_item.items():
            curr_qty = current_by_item.get(name, 0)
            if prev_qty == 0:
                continue
            delta = (curr_qty - prev_qty) / prev_qty
            if delta <= -self.config.sales_drop_threshold:
                priority = Priority.CRITICAL if delta <= -0.5 else Priority.WARNING
                insights.append(RawInsight(
                    detector="sales_anomaly",
                    priority=priority,
                    title=f"Падение продаж: {name}",
                    entity_type="nomenclature",
                    entity_id=name,
                    entity_name=name,
                    metric_name="sales_volume",
                    metric_value=curr_qty,
                    metric_baseline=prev_qty,
                    metric_delta_percent=round(delta * 100, 1),
                    period_from=month_ago,
                    period_to=today,
                    context={
                        "current_qty": curr_qty,
                        "previous_qty": prev_qty,
                        "direction": "drop",
                    },
                    tenant_id=tenant_id,
                ))

        logger.info("SalesAnomalyDetector: найдено {} аномалий", len(insights))
        return insights
