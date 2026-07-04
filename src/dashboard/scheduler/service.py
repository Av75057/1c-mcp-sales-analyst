from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from src.dashboard.composite.service import _get_db
from src.logger import logger


class SchedulerService:
    def create(self, dashboard_id: str, owner_id: str, cron: str = "0 9 * * 1", recipients: list[str] | None = None, format: str = "csv") -> dict[str, Any]:
        conn = _get_db()
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        next_run = self._compute_next(cron)
        try:
            conn.execute(
                "INSERT INTO scheduled_reports (id, dashboard_id, owner_id, cron, recipients, format, is_active, next_run, created_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (sid, dashboard_id, owner_id, cron, json.dumps(recipients or []), format, next_run, now),
            )
            conn.commit()
            return self.get(sid) or {}
        finally:
            conn.close()

    def get(self, sid: str) -> dict[str, Any] | None:
        conn = _get_db()
        try:
            row = conn.execute("SELECT * FROM scheduled_reports WHERE id = ?", (sid,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["recipients"] = json.loads(d.get("recipients", "[]"))
            d["is_active"] = bool(d["is_active"])
            return d
        finally:
            conn.close()

    def list_by_dashboard(self, dashboard_id: str) -> list[dict[str, Any]]:
        conn = _get_db()
        try:
            rows = conn.execute("SELECT * FROM scheduled_reports WHERE dashboard_id = ? ORDER BY created_at DESC", (dashboard_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def list_due(self, limit: int = 20) -> list[dict[str, Any]]:
        conn = _get_db()
        try:
            now = datetime.now(timezone.utc).isoformat()
            rows = conn.execute("SELECT * FROM scheduled_reports WHERE is_active = 1 AND next_run <= ? ORDER BY next_run ASC LIMIT ?", (now, limit)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update(self, sid: str, **kwargs: Any) -> dict[str, Any] | None:
        conn = _get_db()
        try:
            sets = []
            params: list[Any] = []
            for k, v in kwargs.items():
                if k == "recipients":
                    v = json.dumps(v)
                sets.append(f"{k} = ?")
                params.append(v)
            if not sets:
                return self.get(sid)
            params.append(sid)
            conn.execute(f"UPDATE scheduled_reports SET {', '.join(sets)} WHERE id = ?", params)
            conn.commit()
            return self.get(sid)
        finally:
            conn.close()

    def mark_run(self, sid: str) -> None:
        conn = _get_db()
        try:
            row = conn.execute("SELECT cron FROM scheduled_reports WHERE id = ?", (sid,)).fetchone()
            if not row:
                return
            now = datetime.now(timezone.utc).isoformat()
            next_run = self._compute_next(row["cron"])
            conn.execute("UPDATE scheduled_reports SET last_run = ?, next_run = ? WHERE id = ?", (now, next_run, sid))
            conn.commit()
        finally:
            conn.close()

    def delete(self, sid: str) -> bool:
        conn = _get_db()
        try:
            r = conn.execute("DELETE FROM scheduled_reports WHERE id = ?", (sid,))
            conn.commit()
            return r.rowcount > 0
        finally:
            conn.close()

    def _compute_next(self, cron: str) -> str:
        try:
            from croniter import croniter
            base = datetime.now(timezone.utc)
            cron_iter = croniter(cron, base)
            return cron_iter.get_next(datetime).isoformat()
        except ImportError:
            return ""
        except Exception as e:
            logger.warning("[Scheduler] Failed to compute next run for cron '{}': {}", cron, e)
            return ""


scheduler_service = SchedulerService()
