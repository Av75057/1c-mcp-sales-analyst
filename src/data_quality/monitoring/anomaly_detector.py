from __future__ import annotations

from typing import Any


def detect_anomalies(data: list[dict[str, Any]], field: str, threshold: float = 3.0) -> list[dict[str, Any]]:
    """Обнаружение аномалий через z-score."""
    values = [row[field] for row in data if field in row and isinstance(row[field], (int, float))]
    if len(values) < 5:
        return []

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std = variance ** 0.5
    if std == 0:
        return []

    anomalies = []
    for i, row in enumerate(data):
        if field in row and isinstance(row[field], (int, float)):
            z = abs(row[field] - mean) / std
            if z > threshold:
                anomalies.append({"index": i, "field": field, "value": row[field], "z_score": round(z, 2), "mean": round(mean, 2), "severity": "high" if z > 5 else "medium"})
    return anomalies


def detect_duplicates(data: list[dict[str, Any]], key_fields: list[str]) -> list[dict[str, Any]]:
    """Обнаружение дубликатов по ключевым полям."""
    seen: dict[tuple, int] = {}
    duplicates: list[dict[str, Any]] = []
    for i, row in enumerate(data):
        key = tuple(str(row.get(f, "")) for f in key_fields)
        if key in seen:
            duplicates.append({"index": i, "duplicate_of": seen[key], "key_fields": dict(zip(key_fields, key))})
        else:
            seen[key] = i
    return duplicates


def check_business_rules(data: list[dict[str, Any]], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Проверка бизнес-правил."""
    violations: list[dict[str, Any]] = []
    for i, row in enumerate(data):
        for rule in rules:
            try:
                if not rule["check"](row):
                    violations.append({"index": i, "rule": rule["name"], "message": rule["message"], "severity": "error"})
            except Exception:
                violations.append({"index": i, "rule": rule["name"], "message": "Ошибка проверки", "severity": "warning"})
    return violations
