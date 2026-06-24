from __future__ import annotations

import base64
from datetime import date
from typing import Any

import httpx

from src.config import settings
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

    base_url = settings.c1_base_url.rstrip("/")
    api_url = base_url.replace("/hs/api", "/hs/api/v1")

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

    raw = f"{settings.c1_username}:{settings.c1_password}".encode("utf-8")
    auth_header = "Basic " + base64.b64encode(raw).decode("ascii")

    try:
        async with httpx.AsyncClient(
            headers={"Authorization": auth_header},
            timeout=httpx.Timeout(30.0, connect=10.0),
        ) as client:
            resp = await client.get(f"{api_url}/documents/sales", params=params)
            if resp.status_code == 200:
                return resp.json()
            logger.error("Ошибка 1С {}: {}", resp.status_code, resp.text[:500])
            return {"documents": [], "pagination": {"page": page, "page_size": page_size, "total_count": 0, "total_pages": 0}, "error": resp.text[:500]}
    except Exception as e:
        logger.error("Ошибка запроса к 1С: {}", e)
        return {"documents": [], "pagination": {"page": page, "page_size": page_size, "total_count": 0, "total_pages": 0}, "error": str(e)}
