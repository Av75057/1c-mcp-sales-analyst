from __future__ import annotations

import re
from typing import Any


def validate_object_name(name: str) -> str:
    if not re.match(r'^[А-Яа-яЁёA-Za-z0-9_.]+$', name):
        raise ValueError(f"Недопустимое имя объекта: {name}")
    return name


def validate_fields_list(fields: list[str]) -> None:
    if not fields:
        raise ValueError("Список полей не может быть пустым")
    if len(fields) > 50:
        raise ValueError("Слишком много полей (максимум 50)")
    for field in fields:
        if not re.match(r'^[А-Яа-яЁёA-Za-z0-9_]+$', field):
            raise ValueError(f"Недопустимое имя поля: {field}")


def quote_value(value: Any) -> str:
    if isinstance(value, str):
        return f'"{value.replace("\"", "\"\"")}"'
    elif isinstance(value, bool):
        return "ИСТИНА" if value else "ЛОЖЬ"
    elif isinstance(value, (int, float)):
        return str(value)
    raise ValueError(f"Неподдерживаемый тип: {type(value)}")


def build_query(object_name: str, fields: list[str], filters: dict[str, Any] | None = None, order_by: list[str] | None = None, limit: int = 1000) -> str:
    validate_object_name(object_name)
    validate_fields_list(fields)

    lines = [f"ВЫБРАТЬ", ", ".join(f"Т.{f}" for f in fields), "ИЗ", f"{object_name} КАК Т"]

    if filters:
        clauses = []
        for field, condition in filters.items():
            if isinstance(condition, dict):
                op_map = {">": ">", "<": "<", ">=": ">=", "<=": "<=", "=": "=", "<>": "<>", "LIKE": "ПОДОБНО"}
                sub = [f"Т.{field} {op_map.get(k, k)} {quote_value(v)}" for k, v in condition.items()]
                clauses.append(" И ".join(sub))
            else:
                clauses.append(f"Т.{field} = {quote_value(condition)}")
        lines.append("ГДЕ")
        lines.append(" И ".join(clauses))

    if order_by:
        lines.append("УПОРЯДОЧИТЬ ПО")
        lines.append(", ".join(order_by))

    lines.append(f"ПРЕД {limit}")
    return "\n".join(lines)
