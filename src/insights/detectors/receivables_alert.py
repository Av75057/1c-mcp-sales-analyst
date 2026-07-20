from __future__ import annotations

from datetime import date, timedelta

from src.insights.detectors.base import BaseDetector
from src.insights.models import Priority, RawInsight
from src.logger import logger


class ReceivablesAlertDetector(BaseDetector):
    async def detect(self, tenant_id: str = "default") -> list[RawInsight]:
        logger.info("ReceivablesAlertDetector: запуск")
        from src.tools import get_client
        client = get_client()

        receivables = await client.get_receivables()
        if not receivables:
            logger.info("ReceivablesAlertDetector: нет данных")
            return []

        insights: list[RawInsight] = []
        for r in receivables:
            amount = r.get("amount", 0)
            overdue = r.get("overdue_days", 0)
            if amount <= 0:
                continue
            priority = Priority.CRITICAL if overdue > 60 or amount > 300000 else Priority.WARNING if overdue > 30 else Priority.INFO
            insights.append(RawInsight(
                detector="receivables_alert",
                priority=priority,
                title=f"Задолженность: {r.get('client', '')}",
                entity_type="client",
                entity_id=r.get("client", ""),
                entity_name=r.get("client", ""),
                metric_name="receivables_amount",
                metric_value=amount,
                metric_baseline=100000.0,
                metric_delta_percent=round((amount / 100000.0 - 1) * 100, 1),
                period_from=date.today() - timedelta(days=overdue),
                period_to=date.today(),
                context={
                    "amount": amount,
                    "overdue_days": overdue,
                },
                tenant_id=tenant_id,
            ))

        logger.info("ReceivablesAlertDetector: найдено {} задолженностей", len(insights))
        return insights
