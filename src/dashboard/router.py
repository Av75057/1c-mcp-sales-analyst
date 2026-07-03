from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, HTTPException, Request

from src.dashboard.llm_service import generate_chart_config
from src.dashboard.schemas import ChartConfig, DashboardRequest, DashboardResponse
from src.logger import logger

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


async def _fetch_data(config: ChartConfig) -> list[dict]:
    """Fetch data from 1С based on chart config."""
    from datetime import date, timedelta

    periods = {"last_7_days": 7, "last_30_days": 30, "last_quarter": 90, "last_year": 365}
    days = periods.get(config.onec_query.period, 30)
    date_from = (date.today() - timedelta(days=days)).isoformat()
    date_to = date.today().isoformat()

    # Use batch client for flexible queries
    from src.clients.c1_client import C1Client

    c1 = C1Client()
    try:
        sales = await c1.get_sales(date_from=date_from, date_to=date_to)
    finally:
        await c1.close()

    if not sales:
        return []

    fields = config.onec_query.fields
    result = []
    for s in sales:
        row = {}
        for f in fields:
            field_map = {"Дата": "date", "Сумма": "sum", "Количество": "quantity", "Номенклатура": "nomenclature", "Контрагент": "client", "Менеджер": "manager"}
            row[f] = s.get(field_map.get(f, f.lower()), "")
        result.append(row)

    # Aggregation
    agg = config.onec_query.aggregation
    if config.group_by:
        from collections import defaultdict

        grouped: dict[str, dict] = defaultdict(lambda: {"count": 0, "sum": 0.0})
        for row in result:
            key = str(tuple(row.get(g, "") for g in config.group_by))
            grouped[key]["count"] += 1
            for s in config.series:
                grouped[key][s.field] = grouped[key].get(s.field, 0) + float(row.get(s.field, 0))
        result = []
        for key, vals in grouped.items():
            parts = key.strip("()").split(", ")
            row = {}
            for i, g in enumerate(config.group_by):
                row[g] = parts[i] if i < len(parts) else ""
            for s in config.series:
                row[s.field] = round(vals.get(s.field, 0), 2) if agg == "sum" else vals.get("count", 0)
            result.append(row)

    # Sort
    order = config.order_by
    if order and order.get("field"):
        rev = order.get("direction", "desc") == "desc"
        result.sort(key=lambda r: float(r.get(order["field"], 0)), reverse=rev)

    return result[: config.limit]


@router.post("/generate")
async def generate_dashboard(body: DashboardRequest, request: Request = None):
    from src.dashboard.services.history_service import history_service

    req_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    user_id = "api"

    try:
        config = await generate_chart_config(body.query)
        data = await _fetch_data(config)
        elapsed = (time.perf_counter() - start) * 1000

        history_service.log(user_id=user_id, query=body.query, chart_type=config.chart_type, status="success", execution_time_ms=int(elapsed))

        return DashboardResponse(
            chart=config.model_dump(),
            data=data,
            meta={"query_time_ms": round(elapsed, 2), "rows_count": len(data), "request_id": req_id},
        )

    except ValueError as e:
        history_service.log(user_id=user_id, query=body.query, chart_type=None, status="error", error_code="INVALID_QUERY")
        return DashboardResponse(status="error", error_code="INVALID_QUERY", message=str(e), suggestions=["Покажи продажи за последний месяц", "Топ-10 товаров по выручке"])
    except Exception as e:
        logger.error("[Dashboard] Error: {}", e)
        history_service.log(user_id=user_id, query=body.query, chart_type=None, status="error", error_code="NO_DATA")
        return DashboardResponse(status="error", error_code="NO_DATA", message="По вашему запросу данных не найдено.", suggestions=["Попробуйте расширить период", "Проверьте правильность названия"])
