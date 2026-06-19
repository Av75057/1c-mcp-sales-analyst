from __future__ import annotations

from datetime import date, timedelta

from src.clients.c1_client import C1Client
from src.insights.detectors.base import BaseDetector
from src.insights.models import Priority, RawInsight
from src.logger import logger


class InactiveClientsDetector(BaseDetector):
    async def detect(self, tenant_id: str = "default") -> list[RawInsight]:
        logger.info("InactiveClientsDetector: запуск")
        client = C1Client()
        today = date.today()
        year_ago = today - timedelta(days=365)
        month_ago = today - timedelta(days=30)

        sales = await client.get_sales(
            date_from=year_ago.isoformat(),
            date_to=today.isoformat(),
        )

        if not sales:
            return []

        client_last_date: dict[str, date] = {}
        client_intervals: dict[str, list[int]] = {}

        for s in sales:
            mgr = s.get("manager", "") or "Неизвестно"
            d_str = s.get("date", "")
            try:
                d = date.fromisoformat(d_str)
            except (ValueError, TypeError):
                continue
            if mgr not in client_last_date or d > client_last_date[mgr]:
                client_last_date[mgr] = d

        current_month = [s for s in sales if (s.get("date", "") or "")[:7] == today.isoformat()[:7]]
        active_managers = set(s.get("manager", "") for s in current_month)

        insights: list[RawInsight] = []
        for mgr, last_date in client_last_date.items():
            if mgr in active_managers:
                continue
            days_since = (today - last_date).days
            if days_since >= 30:
                insights.append(RawInsight(
                    detector="inactive_clients",
                    priority=Priority.WARNING if days_since < 60 else Priority.CRITICAL,
                    title=f"Менеджер не активен: {mgr}",
                    entity_type="manager",
                    entity_id=mgr,
                    entity_name=mgr,
                    metric_name="days_inactive",
                    metric_value=float(days_since),
                    metric_baseline=14.0,
                    metric_delta_percent=round((days_since / 14.0 - 1) * 100, 1),
                    period_from=last_date,
                    period_to=today,
                    context={"days_since_last_sale": days_since, "last_sale_date": last_date.isoformat()},
                    tenant_id=tenant_id,
                ))

        logger.info("InactiveClientsDetector: найдено {} неактивных", len(insights))
        return insights
