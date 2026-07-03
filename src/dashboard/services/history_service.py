from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from src.dashboard.storage.models import _get_db


class HistoryService:
    def log(self, user_id: str, query: str, chart_type: str | None = None, status: str = "success", error_code: str | None = None, execution_time_ms: int | None = None, saved_as_dashboard_id: str | None = None) -> dict[str, Any]:
        conn = _get_db()
        hid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        try:
            conn.execute("INSERT INTO query_history (id, user_id, query, chart_type, status, error_code, execution_time_ms, saved_as_dashboard_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (hid, user_id, query, chart_type, status, error_code, execution_time_ms, saved_as_dashboard_id, now))
            conn.commit()
            return {"id": hid, "query": query, "status": status, "created_at": now}
        finally:
            conn.close()

    def list(self, user_id: str, limit: int = 50, search: str = "") -> list[dict[str, Any]]:
        conn = _get_db()
        try:
            if search:
                rows = conn.execute("SELECT * FROM query_history WHERE user_id = ? AND query LIKE ? ORDER BY created_at DESC LIMIT ?", (user_id, f"%{search}%", limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM query_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get(self, history_id: str) -> dict[str, Any] | None:
        conn = _get_db()
        try:
            row = conn.execute("SELECT * FROM query_history WHERE id = ?", (history_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def link(self, history_id: str, dashboard_id: str) -> None:
        conn = _get_db()
        try:
            conn.execute("UPDATE query_history SET saved_as_dashboard_id = ? WHERE id = ?", (dashboard_id, history_id))
            conn.commit()
        finally:
            conn.close()


history_service = HistoryService()
