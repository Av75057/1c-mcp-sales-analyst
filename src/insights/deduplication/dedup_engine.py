from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.insights.models import RawInsight, TenantInsightsConfig
from src.logger import logger

SENT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sent_insights"


class DedupEngine:
    def __init__(self, config: TenantInsightsConfig | None = None) -> None:
        self.config = config or TenantInsightsConfig()
        SENT_DIR.mkdir(parents=True, exist_ok=True)

    def _sent_path(self, dedup_key: str) -> Path:
        safe = dedup_key.replace(":", "_").replace("/", "_")
        return SENT_DIR / f"{safe}.json"

    def was_sent(self, raw: RawInsight) -> bool:
        path = self._sent_path(raw.dedup_key)
        if not path.exists():
            return False

        try:
            data: dict[str, Any] = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return False

        sent_at = datetime.fromisoformat(data.get("sent_at", ""))
        priority_str = raw.priority.value if hasattr(raw.priority, "value") else raw.priority
        silence_hours = self.config.silence_period_hours.get(priority_str, 24)
        elapsed = (datetime.now(timezone.utc) - sent_at).total_seconds() / 3600
        return elapsed < silence_hours

    def mark_sent(self, raw: RawInsight) -> None:
        path = self._sent_path(raw.dedup_key)
        data = {
            "dedup_key": raw.dedup_key,
            "detector": raw.detector,
            "entity_id": raw.entity_id,
            "metric_name": raw.metric_name,
            "priority": raw.priority.value if hasattr(raw.priority, "value") else raw.priority,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "title": raw.title,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        logger.debug("Dedup: marked sent {}", raw.dedup_key)

    def should_send(self, raw: RawInsight) -> bool:
        return not self.was_sent(raw)

    def clean_old(self, days: int = 30) -> int:
        """Remove sent marks older than N days"""
        now = datetime.now(timezone.utc)
        count = 0
        for path in SENT_DIR.glob("*.json"):
            try:
                data: dict = json.loads(path.read_text())
                sent_at = datetime.fromisoformat(data.get("sent_at", ""))
                if (now - sent_at).days > days:
                    path.unlink()
                    count += 1
            except (json.JSONDecodeError, OSError):
                path.unlink()
                count += 1
        if count:
            logger.info("Dedup: cleaned {} old entries", count)
        return count
