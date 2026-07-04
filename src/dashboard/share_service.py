from __future__ import annotations

import base64
import io
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.logger import logger

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "dashboards.db"


class ShareService:
    """Шаринг дашбордов: публичные ссылки с токенами и QR-кодами."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(DB_PATH)
        self._init_db()

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_shares (
                    id TEXT PRIMARY KEY,
                    dashboard_id TEXT NOT NULL,
                    share_token TEXT UNIQUE NOT NULL,
                    permissions TEXT NOT NULL DEFAULT 'view' CHECK(permissions IN ('view', 'edit')),
                    shared_by TEXT NOT NULL,
                    expires_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_shares_token ON dashboard_shares(share_token)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_shares_dashboard ON dashboard_shares(dashboard_id)")
            conn.commit()
        finally:
            conn.close()

    def create(self, dashboard_id: str, shared_by: str, permissions: str = "view", expires_in_days: int | None = 30) -> dict[str, Any]:
        conn = self._connect()
        sid = str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(days=expires_in_days)).isoformat() if expires_in_days else None
        try:
            conn.execute(
                "INSERT INTO dashboard_shares (id, dashboard_id, share_token, permissions, shared_by, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                (sid, dashboard_id, token, permissions, shared_by, expires_at),
            )
            conn.commit()
            return {
                "share_id": sid,
                "share_token": token,
                "share_url": f"/share/{token}",
                "permissions": permissions,
                "expires_at": expires_at,
                "qr_code": self._generate_qr(token),
            }
        finally:
            conn.close()

    def get_by_token(self, token: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM dashboard_shares WHERE share_token = ? AND is_active = 1",
                (token,),
            ).fetchone()
            if not row:
                return None
            share = dict(row)
            if share["expires_at"]:
                expires = datetime.fromisoformat(share["expires_at"])
                if datetime.now(timezone.utc) > expires:
                    conn.execute("UPDATE dashboard_shares SET is_active = 0 WHERE id = ?", (share["id"],))
                    conn.commit()
                    return None
            return share
        finally:
            conn.close()

    def revoke(self, share_id: str) -> bool:
        conn = self._connect()
        try:
            r = conn.execute("UPDATE dashboard_shares SET is_active = 0 WHERE id = ?", (share_id,))
            conn.commit()
            return r.rowcount > 0
        finally:
            conn.close()

    def revoke_by_dashboard(self, dashboard_id: str) -> None:
        conn = self._connect()
        try:
            conn.execute("UPDATE dashboard_shares SET is_active = 0 WHERE dashboard_id = ?", (dashboard_id,))
            conn.commit()
        finally:
            conn.close()

    def list_for_dashboard(self, dashboard_id: str) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM dashboard_shares WHERE dashboard_id = ? ORDER BY created_at DESC",
                (dashboard_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def _generate_qr(self, token: str) -> str:
        """Генерирует QR-код для ссылки и возвращает как base64 PNG."""
        try:
            import qrcode
            from PIL import Image
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(f"/share/{token}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()
        except ImportError:
            logger.warning("qrcode not installed, skipping QR generation")
            return ""

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn


share_service = ShareService()
