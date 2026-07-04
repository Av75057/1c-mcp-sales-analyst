from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from src.config import settings
from src.logger import logger


def _get_client():
    if settings.use_mock_data:
        from src.clients.mock_c1_client import MockC1Client
        return MockC1Client()
    from src.clients.c1_client import C1Client
    return C1Client()


DELIM = "\x00"

def _group_data(rows: list[dict], group_fields: list[str], series_fields: list[str], aggregation: str) -> list[dict]:
    """Группировка данных по полям с суммированием."""
    if not group_fields or not rows:
        return rows

    grouped: dict[str, dict] = defaultdict(lambda: {"__count": 0})
    for row in rows:
        key = DELIM.join(str(row.get(g, "")) for g in group_fields)
        grouped[key]["__count"] += 1
        for sf in series_fields:
            if sf:
                try:
                    grouped[key][sf] = grouped[key].get(sf, 0) + float(row.get(sf, 0) or 0)
                except (ValueError, TypeError):
                    pass

    result = []
    for key, vals in grouped.items():
        parts = key.split(DELIM)
        row: dict[str, Any] = {}
        for i, g in enumerate(group_fields):
            row[g] = parts[i] if i < len(parts) else ""
        for sf in series_fields:
            if sf:
                row[sf] = round(vals.get(sf, 0), 2) if aggregation == "sum" else vals.get("__count", 0)
        result.append(row)
    return result


async def fetch_chart_data(chart_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Загрузка данных из 1С по конфигурации графика."""
    cfg = chart_config or {}
    onec = cfg.get("onec_query", {})
    if not onec:
        return []

    periods = {"last_7_days": 7, "last_30_days": 30, "last_quarter": 90, "last_year": 365}
    days = periods.get(onec.get("period", ""), 30)
    date_from = onec.get("date_from", (date.today() - timedelta(days=days)).isoformat())
    date_to = onec.get("date_to", date.today().isoformat())
    fields = onec.get("fields", [])
    aggregation = onec.get("aggregation", "sum")
    chart_type = cfg.get("chart_type", "bar")

    client = _get_client()
    try:
        sales = await client.get_sales(date_from=date_from, date_to=date_to)
    finally:
        if hasattr(client, "close"):
            await client.close()

    if not sales:
        return []

    field_map = {"Дата": "date", "Сумма": "sum", "Количество": "quantity", "Номенклатура": "nomenclature", "Контрагент": "client", "Менеджер": "manager", "Период": "date"}
    result = []
    for s in sales:
        row = {}
        for f in fields:
            mapped = field_map.get(f, f.lower())
            row[f] = s.get(mapped, str(s.get(mapped, "")))
        result.append(row)

    # Группировка: явная из конфига или автоматическая для pie/horizontal_bar/bar
    group_by = cfg.get("group_by", [])
    series_fields = [s.get("field", "") for s in cfg.get("series", [])]

    if not group_by and chart_type in ("pie", "horizontal_bar"):
        cat_field = cfg.get("x_axis", {}).get("field", "")
        if cat_field and cat_field in fields:
            group_by = [cat_field]

    if group_by:
        result = _group_data(result, group_by, series_fields, aggregation)

    # Сортировка
    order = cfg.get("order_by", {})
    if order and order.get("field"):
        field = order["field"]
        rev = order.get("direction", "desc") == "desc"
        result.sort(key=lambda r: float(r.get(field, 0) or 0), reverse=rev)

    limit = cfg.get("limit", 50)
    if chart_type == "pie":
        limit = min(limit, 7)  # не больше 7 сегментов в пироге

    return result[:limit]
