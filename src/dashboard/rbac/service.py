from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.dashboard.composite.service import _get_db


class RBACService:
    def set_permission(self, dashboard_id: str, user_id: str, permission: str = "view") -> dict[str, Any]:
        conn = _get_db()
        pid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO dashboard_permissions (id, dashboard_id, user_id, permission, created_at) VALUES (?, ?, ?, ?, ?)",
                (pid, dashboard_id, user_id, permission, now),
            )
            conn.commit()
            return {"id": pid, "dashboard_id": dashboard_id, "user_id": user_id, "permission": permission}
        finally:
            conn.close()

    def get_permission(self, dashboard_id: str, user_id: str) -> str | None:
        conn = _get_db()
        try:
            row = conn.execute("SELECT permission FROM dashboard_permissions WHERE dashboard_id = ? AND user_id = ?", (dashboard_id, user_id)).fetchone()
            return row["permission"] if row else None
        finally:
            conn.close()

    def list_permissions(self, dashboard_id: str) -> list[dict[str, Any]]:
        conn = _get_db()
        try:
            rows = conn.execute("SELECT user_id, permission, created_at FROM dashboard_permissions WHERE dashboard_id = ?", (dashboard_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def remove_permission(self, dashboard_id: str, user_id: str) -> bool:
        conn = _get_db()
        try:
            r = conn.execute("DELETE FROM dashboard_permissions WHERE dashboard_id = ? AND user_id = ?", (dashboard_id, user_id))
            conn.commit()
            return r.rowcount > 0
        finally:
            conn.close()

    def can_access(self, dashboard_id: str, user_id: str, required: str = "view") -> bool:
        conn = _get_db()
        try:
            row = conn.execute("SELECT owner_id, is_public FROM composite_dashboards WHERE id = ?", (dashboard_id,)).fetchone()
            if not row:
                return False
            if row["owner_id"] == user_id:
                return True
            if row["is_public"] and required == "view":
                return True
            perm = conn.execute("SELECT permission FROM dashboard_permissions WHERE dashboard_id = ? AND user_id = ?", (dashboard_id, user_id)).fetchone()
            if not perm:
                return False
            levels = {"view": 0, "edit": 1, "admin": 2}
            return levels.get(perm["permission"], -1) >= levels.get(required, 0)
        finally:
            conn.close()


rbac_service = RBACService()
