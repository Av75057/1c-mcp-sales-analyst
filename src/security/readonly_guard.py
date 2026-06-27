from __future__ import annotations

import re

FORBIDDEN_KEYWORDS = [
    "ИЗМЕНЕНИЕ", "ИЗМЕНИТЬ", "ДОБАВИТЬ", "ДОБАВЛЕНИЕ", "УДАЛИТЬ", "УДАЛЕНИЕ",
    "ПОМЕТИТЬУДАЛЕНИЕ", "СНЯТЬПОМЕТКУУДАЛЕНИЯ", "ПРОВЕСТИ", "ОТМЕНАПРОВОДКИ",
    "ЗАПИСАТЬ", "UPDATE", "INSERT", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE",
]


class ReadOnlyGuardError(Exception):
    pass


def validate_query(query: str) -> bool:
    normalized = re.sub(r'//.*?$', '', query, flags=re.MULTILINE)
    normalized = re.sub(r'"[^"]*"', '', normalized)
    normalized = normalized.upper()

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', normalized):
            raise ReadOnlyGuardError(f"Запрещённая операция: {keyword}. Разрешены только операции чтения.")

    if ";" in normalized:
        stmts = [s.strip() for s in normalized.split(";") if s.strip()]
        if len(stmts) > 1:
            raise ReadOnlyGuardError("Множественные запросы запрещены.")

    return True
