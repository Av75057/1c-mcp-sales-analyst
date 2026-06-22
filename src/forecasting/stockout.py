from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.forecasting.models import auto_select


async def predict_stockout(
    stock_data: list[dict[str, Any]],
    sales_data: list[dict[str, Any]],
    lead_time_days: int = 7,
    safety_stock_days: int = 3,
    days_horizon: int = 60,
) -> dict[str, Any]:
    import pandas as pd

    sales_df = pd.DataFrame(sales_data)
    if sales_df.empty:
        return {"error": "Нет данных о продажах", "critical": [], "summary": {"total": 0, "critical": 0}}

    today = date.today()
    critical: list[dict[str, Any]] = []
    upcoming: list[dict[str, Any]] = []
    safe: list[dict[str, Any]] = []
    items_processed = 0

    stock_items = {(s.get("nomenclature") or s.get("item", "")): s.get("quantity", 0) for s in stock_data}
    if "item" in sales_df.columns:
        sales_df["nomenclature"] = sales_df["item"]
    sales_by_item = sales_df.groupby("nomenclature")["quantity"].sum().to_dict()
    avg_daily = {k: v / max(len(sales_data), 1) for k, v in sales_by_item.items()}

    for item_name, current_stock in stock_items.items():
        if current_stock <= 0:
            continue
        avg_daily_consumption = avg_daily.get(item_name, 0)
        if avg_daily_consumption <= 0:
            continue
        days_remaining = current_stock / avg_daily_consumption if avg_daily_consumption > 0 else 999
        is_critical = days_remaining <= lead_time_days + safety_stock_days
        is_upcoming = days_remaining <= days_horizon

        entry = {
            "item": item_name,
            "current_stock": int(current_stock),
            "avg_daily_consumption": round(avg_daily_consumption, 1),
            "days_until_stockout": round(days_remaining, 1),
            "lead_time_days": lead_time_days,
            "status": "CRITICAL" if is_critical else "UPCOMING" if is_upcoming else "SAFE",
            "recommended_order": int(max(0, (lead_time_days + safety_stock_days - days_remaining) * avg_daily_consumption)) if is_critical else 0,
        }
        if entry["recommended_order"] > 0:
            entry["estimated_revenue_loss"] = round(entry["recommended_order"] * 100, 0)

        if is_critical:
            critical.append(entry)
        elif is_upcoming:
            upcoming.append(entry)
        else:
            safe.append(entry)
        items_processed += 1

    critical.sort(key=lambda x: x["days_until_stockout"])
    upcoming.sort(key=lambda x: x["days_until_stockout"])

    return {
        "summary": {"total_items_analyzed": items_processed, "critical_stockouts": len(critical), "upcoming_stockouts": len(upcoming), "safe_items": len(safe)},
        "critical": critical[:20],
        "upcoming": upcoming[:30],
        "recommendations": [{"priority": "high", "action": f"Немедленно заказать {len(critical)} товаров", "items_count": len(critical)}] if critical else [],
    }
