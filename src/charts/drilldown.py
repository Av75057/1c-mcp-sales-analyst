from __future__ import annotations

from typing import Any

from src.logger import logger

# Domain level mappings: how to drill down from one level to the next
# Each domain defines (parent_level -> child_level) query strategies
DOMAIN_STRATEGIES: dict[str, dict[str, Any]] = {
    "sales_by_category": {
        "query": "sales",
        "group_fields": {
            "category": "nomenclature",  # group by item name (top-level)
            "subcategory": "nomenclature",  # filtered by parent item
            "sku": "nomenclature",
        },
    },
    "sales_by_customer": {
        "query": "sales",
        "group_fields": {
            "segment": "client",
            "customer": "client",
        },
    },
    "sales_by_territory": {
        "query": "sales",
        "group_fields": {
            "region": "warehouse",
            "city": "warehouse",
            "store": "warehouse",
            "manager": "manager",
            "sku": "nomenclature",
        },
    },
    "time": {
        "query": "sales",
        "group_fields": {
            "year": "date",
            "quarter": "date",
            "month": "date",
            "week": "date",
            "day": "date",
        },
    },
}


def _group_by_time_period(sales: list[dict], period: str) -> dict[str, float]:
    """Group sales by time period."""
    from collections import defaultdict
    groups: dict[str, float] = defaultdict(float)
    for s in sales:
        date_str = s.get("date", "")
        if not date_str:
            continue
        try:
            parts = date_str[:10].split("-")
            year, month, day = parts[0], parts[1], parts[2]
            if period == "year":
                key = year
            elif period == "quarter":
                q = (int(month) - 1) // 3 + 1
                key = f"{year}-Q{q}"
            elif period == "month":
                key = f"{year}-{month}"
            elif period == "week":
                from datetime import date as dt_date
                d = dt_date(int(year), int(month), int(day))
                iso = d.isocalendar()
                key = f"{year}-W{iso[1]:02d}"
            else:
                key = date_str[:10]
            groups[key] += float(s.get("sum", 0) or 0)
        except (ValueError, IndexError):
            groups[date_str[:10]] += float(s.get("sum", 0) or 0)
    return dict(groups)


def _group_by_field(sales: list[dict], field: str, parent_value: str | None = None, parent_field: str | None = None) -> list[dict]:
    """Group sales by a field, optionally filtered by a parent value."""
    from collections import defaultdict
    groups: dict[str, float] = defaultdict(float)
    for s in sales:
        # Apply parent filter if specified
        if parent_value and parent_field:
            val = str(s.get(parent_field, ""))
            if parent_value.lower() not in val.lower():
                continue
        key = str(s.get(field, "Неизвестно"))
        if not key or key == "Неизвестно":
            continue
        groups[key] += float(s.get("sum", 0) or 0)

    sorted_items = sorted(groups.items(), key=lambda x: -x[1])
    return [{"label": k, "value": round(v, 2)} for k, v in sorted_items[:50]]


async def drill_down(
    domain: str,
    parent_level: str,
    parent_value: str,
    child_level: str,
    date_from: str = "",
    date_to: str = "",
    metric: str = "revenue",
    filters: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Execute a drill-down step: fetch child-level data for a given parent value.

    Args:
        domain: Domain ID (sales_by_category, etc.)
        parent_level: Current level ID
        parent_value: Value at the current level to drill into
        child_level: Target level ID
        date_from: Start date YYYY-MM-DD
        date_to: End date YYYY-MM-DD
        metric: Metric to aggregate (revenue, quantity, etc.)
        filters: Additional filters

    Returns:
        Chart data in create_chart format + breadcrumbs
    """
    logger.info("drill_down: domain={}, parent={}={}, child={}, dates={}-{}",
                domain, parent_level, parent_value, child_level, date_from, date_to)

    strategy = DOMAIN_STRATEGIES.get(domain)
    if not strategy:
        return {"error": f"Unknown domain: {domain}"}

    from src.tools import get_client
    client = get_client()

    # Fetch base data
    try:
        sales = await client.get_sales(
            date_from=date_from or None,
            date_to=date_to or None,
            limit=50000,
        )
    except Exception as e:
        logger.error("drill_down: sales fetch failed: {}", e)
        return {"error": f"Не удалось загрузить данные: {e}"}

    if not sales:
        return {
            "error": f"По «{parent_value}» нет данных за выбранный период",
        }

    # Determine group field for the child level
    domain_config = DOMAIN_STRATEGIES.get(domain, {})
    group_fields = domain_config.get("group_fields", {})
    child_field = group_fields.get(child_level, "nomenclature")
    parent_field = group_fields.get(parent_level)

    if child_level in ("year", "quarter", "month", "week", "day"):
        grouped = _group_by_time_period(sales, child_level)
        table_data = [{"label": k, "value": round(v, 2)} for k, v in sorted(grouped.items())]
    else:
        table_data = _group_by_field(sales, child_field, parent_value, parent_field)

    if not table_data:
        return {
            "error": f"По «{parent_value}» нет дочерних элементов за выбранный период",
        }

    # Determine chart type based on level
    if child_level in ("year", "quarter", "month", "week", "day"):
        chart_type = "line"
    elif len(table_data) <= 8:
        chart_type = "pie"
    else:
        chart_type = "bar"

    x_data = [d["label"] for d in table_data]
    y_data = [d["value"] for d in table_data]

    from src.charts.tool import DRILLDOWN_DOMAINS
    domain_meta = DRILLDOWN_DOMAINS.get(domain, {})
    all_levels = domain_meta.get("levels", [])
    current_idx = next((i for i, l in enumerate(all_levels) if l["id"] == child_level), -1)
    remaining_levels = all_levels[current_idx:] if current_idx >= 0 else []

    result = {
        "table_data": table_data,
        "chart_type": chart_type,
        "title": f"{parent_value} → {child_level}",
        "x_label": child_level,
        "y_label": metric,
        "chart_id": "",
        "breadcrumbs": [
            {"level": parent_level, "label": parent_value},
            {"level": child_level, "label": "..."},
        ],
        "domain_id": domain,
        "drilldown": {
            "enabled": True,
            "domain": domain,
            "current_level": child_level,
            "levels": remaining_levels,
        },
    }

    return result
