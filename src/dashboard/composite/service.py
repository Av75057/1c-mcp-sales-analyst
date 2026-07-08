from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.logger import logger

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "dashboards.db"


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_db()
    try:
        # Миграция: добавить is_favorite если колонки нет
        try:
            conn.execute("ALTER TABLE composite_dashboards ADD COLUMN is_favorite INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # колонка уже есть

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS composite_dashboards (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                charts TEXT NOT NULL DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                is_public INTEGER DEFAULT 0,
                refresh_interval_minutes INTEGER DEFAULT 0,
                is_favorite INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_composite_owner ON composite_dashboards(owner_id);

            CREATE TABLE IF NOT EXISTS dashboard_permissions (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                charts TEXT NOT NULL DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                is_public INTEGER DEFAULT 0,
                refresh_interval_minutes INTEGER DEFAULT 0,
                is_favorite INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_composite_owner ON composite_dashboards(owner_id);
            CREATE INDEX IF NOT EXISTS idx_composite_fav ON composite_dashboards(is_favorite) WHERE is_favorite=1;

            CREATE TABLE IF NOT EXISTS dashboard_permissions (
                id TEXT PRIMARY KEY,
                dashboard_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                permission TEXT NOT NULL DEFAULT 'view',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(dashboard_id, user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_dperm_dash ON dashboard_permissions(dashboard_id);
            CREATE INDEX IF NOT EXISTS idx_dperm_user ON dashboard_permissions(user_id);

            CREATE TABLE IF NOT EXISTS scheduled_reports (
                id TEXT PRIMARY KEY,
                dashboard_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                cron TEXT NOT NULL DEFAULT '0 9 * * 1',
                recipients TEXT NOT NULL DEFAULT '[]',
                format TEXT NOT NULL DEFAULT 'csv',
                is_active INTEGER DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_sched_dash ON scheduled_reports(dashboard_id);

            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                dashboard_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'anomaly',
                title TEXT NOT NULL,
                message TEXT DEFAULT '',
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_notif_read ON notifications(is_read);

            CREATE TABLE IF NOT EXISTS dashboard_recommendations (
                id TEXT PRIMARY KEY,
                dashboard_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                confidence REAL DEFAULT 0.5,
                reason TEXT DEFAULT '',
                suggested_action TEXT DEFAULT '',
                is_applied INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_rec_dash ON dashboard_recommendations(dashboard_id);
        """)
        conn.commit()
    finally:
        conn.close()


class CompositeDashboardService:
    def create(self, owner_id: str, title: str, description: str, charts: list[dict], tags: list[str] | None = None, is_public: bool = False, refresh_interval_minutes: int = 0, is_favorite: bool = False) -> dict[str, Any] | None:
        conn = _get_db()
        doc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            conn.execute(
                "INSERT INTO composite_dashboards (id, owner_id, title, description, charts, tags, is_public, refresh_interval_minutes, is_favorite, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (doc_id, owner_id, title, description, json.dumps(charts, ensure_ascii=False), json.dumps(tags or []), 1 if is_public else 0, refresh_interval_minutes, 1 if is_favorite else 0, now, now),
            )
            conn.commit()
            return self.get(doc_id)
        finally:
            conn.close()

    def get(self, doc_id: str) -> dict[str, Any] | None:
        conn = _get_db()
        try:
            row = conn.execute("SELECT * FROM composite_dashboards WHERE id = ?", (doc_id,)).fetchone()
            if row:
                d = dict(row)
                d["charts"] = json.loads(d.get("charts", "[]"))
                d["tags"] = json.loads(d.get("tags", "[]"))
                d["is_public"] = bool(d["is_public"])
                d["is_favorite"] = bool(d["is_favorite"])
                conn.execute("UPDATE composite_dashboards SET view_count = view_count + 1 WHERE id = ?", (doc_id,))
                conn.commit()
                return d
            # Fallback to old dashboards table
            try:
                old = conn.execute("SELECT * FROM dashboards WHERE id = ?", (doc_id,)).fetchone()
                if old:
                    d = dict(old)
                    cc = json.loads(d.get("chart_config", "{}"))
                    conn.execute("UPDATE dashboards SET view_count = view_count + 1 WHERE id = ?", (doc_id,))
                    conn.commit()
                    return {
                        "id": d["id"], "owner_id": d["owner_id"], "title": d["title"],
                        "description": d.get("description", ""),
                        "charts": [{"id": "c1", "title": d["title"], "chart_config": cc, "data": [], "position": {"x": 0, "y": 0, "w": 6, "h": 4}, "filter_bindings": []}],
                        "tags": json.loads(d.get("tags", "[]")),
                        "is_public": bool(d["is_public"]), "is_favorite": bool(d["is_favorite"]),
                        "view_count": d["view_count"], "refresh_interval_minutes": 0,
                        "created_at": d["created_at"], "updated_at": d["updated_at"],
                    }
            except Exception:
                pass
            return None
        finally:
            conn.close()

    def list(self, owner_id: str | None = None, search: str = "", page: int = 1, per_page: int = 20) -> dict[str, Any]:
        conn = _get_db()
        try:
            # Если owner_id = "anonymous" или не указан — показываем всё
            show_all = not owner_id or owner_id == "anonymous"

            conditions = ["1=1"]
            params: list[Any] = []
            if owner_id and not show_all:
                conditions.append("c.owner_id = ?")
                params.append(owner_id)
            if search:
                conditions.append("(c.title LIKE ? OR c.description LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])

            where = " AND ".join(conditions)
            total = conn.execute(f"SELECT COUNT(*) as cnt FROM composite_dashboards c WHERE {where}", params).fetchone()["cnt"]

            # Also count old dashboards
            old_conditions = ["1=1"]
            old_params: list[Any] = []
            if owner_id and not show_all:
                old_conditions.append("d.owner_id = ?")
                old_params.append(owner_id)
            if search:
                old_conditions.append("(d.title LIKE ? OR d.description LIKE ?)")
                old_params.extend([f"%{search}%", f"%{search}%"])
            old_where = " AND ".join(old_conditions)
            try:
                old_total = conn.execute(f"SELECT COUNT(*) as cnt FROM dashboards d WHERE {old_where}", old_params).fetchone()["cnt"]
                total += old_total
            except Exception:
                pass

            offset = (page - 1) * per_page
            rows = conn.execute(f"SELECT * FROM composite_dashboards c WHERE {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?", [*params, per_page, offset]).fetchall()
            items = []
            for r in rows:
                d = dict(r)
                d["charts"] = json.loads(d.get("charts", "[]"))
                d["tags"] = json.loads(d.get("tags", "[]"))
                d["is_public"] = bool(d["is_public"])
                d["is_favorite"] = bool(d["is_favorite"])
                items.append(d)

            # Add old dashboards (всегда добавляем, если есть место)
            try:
                old_limit = per_page
                old_offset = max(0, offset - len(items))
                old_rows = conn.execute(
                    "SELECT id, owner_id, title, description, chart_config, tags, is_public, is_favorite, view_count, created_at, updated_at FROM dashboards d WHERE {} ORDER BY updated_at DESC LIMIT ? OFFSET ?".format(old_where),
                    [*old_params, old_limit, old_offset],
                ).fetchall()
                for r in old_rows:
                    d = dict(r)
                    cc = json.loads(d.get("chart_config", "{}"))
                    items.append({
                        "id": d["id"],
                        "owner_id": d["owner_id"],
                        "title": d["title"],
                        "description": d.get("description", ""),
                        "charts": [{"id": "c1", "title": d["title"], "chart_config": cc, "data": [], "position": {"x": 0, "y": 0, "w": 6, "h": 4}, "filter_bindings": []}],
                        "tags": json.loads(d.get("tags", "[]")),
                        "is_public": bool(d["is_public"]),
                        "is_favorite": bool(d["is_favorite"]),
                        "view_count": d["view_count"],
                        "refresh_interval_minutes": 0,
                        "created_at": d["created_at"],
                        "updated_at": d["updated_at"],
                    })
            except Exception:
                pass

            return {"dashboards": items, "total": total, "page": page, "per_page": per_page, "total_pages": max(1, (total + per_page - 1) // per_page)}
        finally:
            conn.close()

    def update(self, doc_id: str, **kwargs: Any) -> dict[str, Any] | None:
        conn = _get_db()
        try:
            sets = []
            params: list[Any] = []
            for k, v in kwargs.items():
                if k == "tags":
                    v = json.dumps(v)
                elif k == "charts":
                    v = json.dumps(v)
                elif k in ("is_public", "is_favorite"):
                    v = 1 if v else 0
                sets.append(f"{k} = ?")
                params.append(v)
            if not sets:
                return self.get(doc_id)
            sets.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
            params.append(doc_id)
            conn.execute(f"UPDATE composite_dashboards SET {', '.join(sets)} WHERE id = ?", params)
            conn.commit()
            return self.get(doc_id)
        finally:
            conn.close()

    def delete(self, doc_id: str) -> bool:
        conn = _get_db()
        try:
            conn.execute("DELETE FROM dashboard_permissions WHERE dashboard_id = ?", (doc_id,))
            conn.execute("DELETE FROM scheduled_reports WHERE dashboard_id = ?", (doc_id,))
            conn.execute("DELETE FROM notifications WHERE dashboard_id = ?", (doc_id,))
            conn.execute("DELETE FROM dashboard_recommendations WHERE dashboard_id = ?", (doc_id,))
            r = conn.execute("DELETE FROM composite_dashboards WHERE id = ?", (doc_id,))
            try:
                conn.execute("DELETE FROM query_history WHERE saved_as_dashboard_id = ?", (doc_id,))
                conn.execute("DELETE FROM dashboard_feedback WHERE dashboard_id = ?", (doc_id,))
                conn.execute("DELETE FROM dashboards WHERE id = ?", (doc_id,))
            except Exception:
                pass
            conn.commit()
            return r.rowcount > 0 or True
        finally:
            conn.close()


composite_service = CompositeDashboardService()
