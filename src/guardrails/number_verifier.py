from __future__ import annotations

import re
from typing import Any

from src.logger import logger


def extract_numbers(text: str) -> list[dict[str, Any]]:
    """Извлекает числа с контекстом из текста."""
    patterns = [
        (r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*(?:руб|₽|р\.)", "currency"),
        (r"(\d+(?:[.,]\d+)?)\s*(%|процента)", "percent"),
        (r"(\d+(?:[.,]\d+)?)\s*(тыс\.?\s*(?:руб|₽)?)", "thousands"),
        (r"(\d+(?:[.,]\d+)?)\s*(млн\.?\s*(?:руб|₽)?)", "millions"),
        (r"на\s+(\d+(?:[.,]\d+)?)\s*%", "percent_change"),
        (r"(\d+(?:[.,]\d+)?)\s*шту?к", "quantity"),
    ]
    results = []
    for pattern, kind in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw = match.group(1)
            value = float(raw.replace(" ", "").replace(",", "."))
            results.append({"value": value, "context": match.group(0), "type": kind, "position": match.start()})
    return results


def find_in_context(value: float, context: Any, tolerance: float = 0.01) -> bool:
    """Рекурсивно ищет число в данных с допуском 1%."""
    if isinstance(context, (int, float)):
        if context == 0 and value == 0:
            return True
        if abs(context) > 0:
            return abs(context - value) / max(abs(context), 0.001) < tolerance
    elif isinstance(context, dict):
        return any(find_in_context(value, v, tolerance) for v in context.values())
    elif isinstance(context, (list, tuple)):
        return any(find_in_context(value, v, tolerance) for v in context)
    return False


class NumberVerifier:
    """Проверяет числа в ответе AI на соответствие данным из 1С."""

    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance

    def verify(self, response: str, context_data: dict[str, Any] | None = None) -> dict[str, Any]:
        numbers = extract_numbers(response)
        issues = []

        if context_data:
            for num_info in numbers:
                if not find_in_context(num_info["value"], context_data, self.tolerance):
                    issues.append({"value": num_info["value"], "context": num_info["context"], "type": "number_not_found_in_data"})

        return {"is_valid": len(issues) == 0, "issues": issues, "checked": len(numbers)}

    def verify_and_log(self, response: str, context_data: dict[str, Any] | None = None) -> dict[str, Any]:
        result = self.verify(response, context_data)
        if not result["is_valid"]:
            logger.warning("[Guardrail] Числа не найдены в данных: {}", result["issues"])
        return result


number_verifier = NumberVerifier()
