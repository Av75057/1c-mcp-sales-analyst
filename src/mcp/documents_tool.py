from __future__ import annotations

from datetime import date
from typing import Any

from src.logger import logger
from src.perf import measure_time


@measure_time("get_sales_documents")
async def get_sales_documents(
    date_from: str = "",
    date_to: str = "",
    counterparty: str | None = None,
    sum_min: float | None = None,
    sum_max: float | None = None,
    posted_only: bool = True,
    sort_by: str = "date",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    logger.info(
        "Вызов get_sales_documents: {}-{}, counterparty={}, page={}",
        date_from, date_to, counterparty, page,
    )

    if date_from and date_to:
        try:
            d_from = date.fromisoformat(date_from)
            d_to = date.fromisoformat(date_to)
            if (d_to - d_from).days > 730:
                return {"error": "period_too_large", "message": "Максимальный период — 2 года. Уменьшите диапазон дат."}
        except ValueError:
            return {"error": "invalid_date", "message": "Неверный формат даты. Используйте YYYY-MM-DD"}

    from src.tools import get_client

    params: dict[str, Any] = {
        "date_from": date_from,
        "date_to": date_to,
        "posted_only": str(posted_only).lower(),
        "sort_by": sort_by,
        "sort_order": sort_order,
        "page": str(page),
        "page_size": str(min(page_size, 500)),
    }
    if counterparty:
        params["counterparty"] = counterparty
    if sum_min is not None:
        params["sum_min"] = str(sum_min)
    if sum_max is not None:
        params["sum_max"] = str(sum_max)

    try:
        client = get_client()
        base = client.base_url.replace("/hs/api", "/hs/api/v1")
        from src.clients.c1_client import C1Client
        if isinstance(client, C1Client):
            resp = await client._request("GET", f"{base}/documents/sales", params=params)
            return resp.json()
        sales = await client.get_sales(date_from=date_from, date_to=date_to)
        return {"documents": [{
            "date": s.get("date", ""),
            "number": s.get("document_number", ""),
            "amount": s.get("sum", 0),
            "counterparty": s.get("client", ""),
            "manager": s.get("manager", ""),
        } for s in sales], "pagination": {"page": page, "page_size": page_size, "total_count": len(sales), "total_pages": 1}}
    except Exception as e:
        logger.error("Ошибка запроса к 1С: {}", e)
        return {"documents": [], "pagination": {"page": page, "page_size": page_size, "total_count": 0, "total_pages": 0}, "error": str(e)}
