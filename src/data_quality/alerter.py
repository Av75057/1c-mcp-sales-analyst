from __future__ import annotations

from typing import Any

from src.logger import logger


class DataQualityAlerter:
    THRESHOLDS = {"quality_score_min": 0.95, "invalid_records_max": 100, "anomaly_count_max": 10}

    async def check(self, report: dict[str, Any]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        score = report.get("quality_score", 1.0)
        if score < self.THRESHOLDS["quality_score_min"]:
            alerts.append({"type": "low_quality_score", "severity": "high", "message": f"Quality score: {score:.1%}"})
        invalid = report.get("total_records", 0) - report.get("valid_records", 0)
        if invalid > self.THRESHOLDS["invalid_records_max"]:
            alerts.append({"type": "too_many_invalid", "severity": "medium", "message": f"Invalid records: {invalid}"})
        for a in alerts:
            logger.warning("[DataQuality Alert] {}: {}", a["type"], a["message"])
        return alerts


data_quality_alerter = DataQualityAlerter()
