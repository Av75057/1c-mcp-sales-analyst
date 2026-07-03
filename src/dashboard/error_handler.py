from __future__ import annotations

from typing import Any

from src.dashboard.guardrails import GuardrailError
from src.logger import logger

DEFAULT_SUGGESTIONS = ["Покажи продажи за последний месяц", "Топ-10 товаров по выручке", "Структура продаж по группам"]


def handle_error(error: Exception, original_query: str = "") -> dict[str, Any]:
    if isinstance(error, GuardrailError):
        return {"status": "error", "error_code": "INVALID_QUERY", "message": str(error), "suggestions": DEFAULT_SUGGESTIONS}

    if "No data" in str(error) or "no data" in str(error).lower():
        return {"status": "error", "error_code": "NO_DATA", "message": "По вашему запросу данных не найдено.", "suggestions": ["Попробуйте расширить период", "Проверьте правильность названия товара/клиента"]}

    if "parse" in str(error).lower() or "JSON" in str(error):
        return {"status": "error", "error_code": "INVALID_QUERY", "message": "Не удалось понять запрос. Попробуйте переформулировать.", "suggestions": DEFAULT_SUGGESTIONS}

    logger.error("[Dashboard] Error: {} (query: {})", error, original_query)
    return {"status": "error", "error_code": "INTERNAL_ERROR", "message": "Произошла внутренняя ошибка. Попробуйте позже."}
