from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from src.dashboard.storage.models import _get_db


class FeedbackService:
    def submit(self, dashboard_id: str, user_id: str, rating: str, comment: str = "", issue_type: str | None = None) -> dict[str, Any]:
        conn = _get_db()
        fid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        try:
            conn.execute("INSERT INTO dashboard_feedback (id, dashboard_id, user_id, rating, comment, issue_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (fid, dashboard_id, user_id, rating, comment, issue_type, now))
            conn.commit()
            return {"id": fid, "rating": rating, "created_at": now}
        finally:
            conn.close()

    def get_stats(self) -> dict[str, Any]:
        conn = _get_db()
        try:
            positive = conn.execute("SELECT COUNT(*) as cnt FROM dashboard_feedback WHERE rating = 'positive'").fetchone()["cnt"]
            negative = conn.execute("SELECT COUNT(*) as cnt FROM dashboard_feedback WHERE rating = 'negative'").fetchone()["cnt"]
            return {"positive": positive, "negative": negative, "total": positive + negative}
        finally:
            conn.close()


feedback_service = FeedbackService()
