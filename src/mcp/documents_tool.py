from __future__ import annotations

from datetime import date, datetime
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
    """Получить список документов реализации из 1С УНФ.

    Args:
        date_from: Дата начала периода (YYYY-MM-DD)
        date_to: Дата окончания периода (YYYY-MM-DD)
        counterparty: Фильтр по контрагенту (подстрока)
        sum_min: Минимальная сумма
        sum_max: Максимальная сумма
        posted_only: Только проведённые документы
        sort_by: Поле сортировки (date|sum|number)
        sort_order: Направление (asc|desc)
        page: Номер страницы (>=1)
        page_size: Размер страницы (1-500)

    Returns:
        dict с ключами documents, pagination
    """
    logger.info(
        "Вызов get_sales_documents: {}-{}, counterparty={}, page={}",
        date_from, date_to, counterparty, page,
    )

    # Валидация периода
    if date_from and date_to:
        try:
            d_from = date.fromisoformat(date_from)
            d_to = date.fromisoformat(date_to)
            if (d_to - d_from).days > 730:
                return {
                    "error": "period_too_large",
                    "message": "Максимальный период — 2 года. Уменьшите диапазон дат.",
                }
        except ValueError:
            return {"error": "invalid_date", "message": "Неверный формат даты. Используйте YYYY-MM-DD"}

    # Формируем batch-запрос
    params: dict[str, Any] = {
        "date_from": date_from,
        "date_to": date_to,
        "posted_only": posted_only,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "page": page,
        "page_size": min(page_size, 500),
    }
    if counterparty:
        params["counterparty"] = counterparty
    if sum_min is not None:
        params["sum_min"] = sum_min
    if sum_max is not None:
        params["sum_max"] = sum_max

    request = {
        "id": "sales_documents",
        "method": "GET",
        "path": "/documents/sales",
        "params": params,
    }

    from src.clients.batch_client import BatchC1Client

    async with BatchC1Client() as client:
        result = await client.execute_batch([request])

    results = result.get("results", [])
    if results:
        data = results[0].get("data", {})
        return data

    return {"documents": [], "pagination": {"page": page, "page_size": page_size, "total_count": 0, "total_pages": 0}}
