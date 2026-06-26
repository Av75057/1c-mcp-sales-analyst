from __future__ import annotations

from typing import Any

from src.data_quality.monitoring.anomaly_detector import detect_anomalies


def compute_quality_report(data: list[dict[str, Any]], tool_name: str = "") -> dict[str, Any]:
    """Вычисляет отчёт о качестве данных."""
    total = len(data)
    issues: list[str] = []
    for item in data:
        for k, v in item.items():
            if isinstance(v, (int, float)) and v < 0:
                issues.append(f"negative_{k}")
            elif isinstance(v, str) and not v.strip() and k in ("nomenclature", "name", "item"):
                issues.append(f"empty_{k}")

    valid = total - len(set(issues))
    return {
        "total_records": total,
        "valid_records": valid,
        "invalid_records": total - valid,
        "quality_score": round(valid / max(total, 1), 3),
        "issues": issues[:20],
        "anomalies": {field: detect_anomalies(data, field) for field in ("sum", "quantity", "price")},
    }
