from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def resolve_period(period: str) -> tuple[date, date]:
    today = date.today()
    periods = {
        "last_7_days": (today - timedelta(days=7), today),
        "last_30_days": (today - timedelta(days=30), today),
        "last_quarter": (today - timedelta(days=90), today),
        "last_year": (today - timedelta(days=365), today),
        "previous_7_days": (today - timedelta(days=14), today - timedelta(days=7)),
        "previous_30_days": (today - timedelta(days=60), today - timedelta(days=30)),
        "previous_quarter": (today - timedelta(days=180), today - timedelta(days=90)),
    }
    return periods.get(period, periods["last_30_days"])


def compute_comparison(config: dict[str, Any]) -> dict[str, Any]:
    if not config.get("comparison", {}).get("enabled"):
        return config

    comp_type = config["comparison"]["type"]
    c_from, c_to = resolve_period(config["onec_query"]["period"])
    comp_from, comp_to = resolve_period("previous_30_days") if comp_type == "previous_period" else (c_from.replace(year=c_from.year - 1), c_to.replace(year=c_to.year - 1))

    config["comparison"]["current_period"] = {"from": c_from.isoformat(), "to": c_to.isoformat()}
    config["comparison"]["comparison_period"] = {"from": comp_from.isoformat(), "to": comp_to.isoformat()}
    config["onec_query"]["comparison_query"] = {"period": "custom", "date_from": comp_from.isoformat(), "date_to": comp_to.isoformat(), "fields": config["onec_query"].get("fields", [])}

    if len(config.get("series", [])) < 2:
        config.setdefault("series", []).append({"name": "Предыдущий период", "field": config["series"][0]["field"] + "_prev", "color": "#91cc75", "type": "line"})
        config["series"][0]["type"] = "bar"
        config["chart_type"] = "combo"

    return config
