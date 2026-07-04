from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.dashboard.bot.service import telegram_bot
from src.dashboard.composite.service import _get_db


class NotificationService:
    def create(self, dashboard_id: str, user_id: str, type: str, title: str, message: str = "") -> dict[str, Any]:
        conn = _get_db()
        nid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            conn.execute(
                "INSERT INTO notifications (id, dashboard_id, user_id, type, title, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nid, dashboard_id, user_id, type, title, message, now),
            )
            conn.commit()

            # Отправка в Telegram
            if type == "anomaly":
                self._safe_telegram(f"⚠️ <b>Аномалия</b>\n{title}\n{message}")
            elif type == "report_ready":
                self._safe_telegram(f"📊 <b>Отчёт готов</b>\n{title}")

            return {"id": nid, "dashboard_id": dashboard_id, "type": type, "title": title, "created_at": now}
        finally:
            conn.close()

    def _safe_telegram(self, text: str) -> None:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(telegram_bot.send_message(text))
        except RuntimeError:
            pass

    def list(self, user_id: str, unread_only: bool = False, limit: int = 50) -> list[dict[str, Any]]:
        conn = _get_db()
        try:
            if unread_only:
                rows = conn.execute("SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def mark_read(self, nid: str) -> bool:
        conn = _get_db()
        try:
            r = conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (nid,))
            conn.commit()
            return r.rowcount > 0
        finally:
            conn.close()

    def mark_all_read(self, user_id: str) -> int:
        conn = _get_db()
        try:
            r = conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user_id,))
            conn.commit()
            return r.rowcount
        finally:
            conn.close()

    def unread_count(self, user_id: str) -> int:
        conn = _get_db()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,)).fetchone()
            return row["cnt"]
        finally:
            conn.close()


notification_service = NotificationService()
