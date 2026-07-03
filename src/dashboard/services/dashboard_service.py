from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from src.dashboard.storage.models import _get_db


class DashboardRepository:
    def create(self, owner_id: str, title: str, query: str, chart_config: dict, description: str = "", tags: list[str] | None = None, is_public: bool = False) -> dict[str, Any]:
        conn = _get_db()
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        try:
            conn.execute(
                "INSERT INTO dashboards (id, owner_id, title, description, original_query, chart_config, tags, is_public, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (doc_id, owner_id, title, description, query, json.dumps(chart_config, ensure_ascii=False), json.dumps(tags or []), 1 if is_public else 0, now, now),
            )
            conn.commit()
            return self.get(doc_id) or {}
        finally:
            conn.close()

    def get(self, doc_id: str) -> dict[str, Any] | None:
        conn = _get_db()
        try:
            row = conn.execute("SELECT * FROM dashboards WHERE id = ?", (doc_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["chart_config"] = json.loads(d.get("chart_config", "{}"))
            d["tags"] = json.loads(d.get("tags", "[]"))
            conn.execute("UPDATE dashboards SET view_count = view_count + 1 WHERE id = ?", (doc_id,))
            conn.commit()
            return d
        finally:
            conn.close()

    def list(self, owner_id: str | None = None, search: str = "", tags: list[str] | None = None, is_favorite: bool | None = None, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        conn = _get_db()
        try:
            conditions = ["1=1"]
            params: list[Any] = []
            if owner_id:
                conditions.append("owner_id = ?")
                params.append(owner_id)
            if search:
                conditions.append("(title LIKE ? OR description LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])
            if is_favorite is not None:
                conditions.append("is_favorite = ?")
                params.append(1 if is_favorite else 0)

            where = " AND ".join(conditions)
            total = conn.execute(f"SELECT COUNT(*) as cnt FROM dashboards WHERE {where}", params).fetchone()["cnt"]
            offset = (page - 1) * per_page
            rows = conn.execute(f"SELECT * FROM dashboards WHERE {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?", [*params, per_page, offset]).fetchall()
            items = []
            for r in rows:
                d = dict(r)
                d["chart_config"] = json.loads(d.get("chart_config", "{}"))
                d["tags"] = json.loads(d.get("tags", "[]"))
                items.append(d)

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
                elif k == "chart_config":
                    v = json.dumps(v)
                elif k == "is_public" or k == "is_favorite":
                    v = 1 if v else 0
                sets.append(f"{k} = ?")
                params.append(v)
            if not sets:
                return self.get(doc_id)
            sets.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(doc_id)
            conn.execute(f"UPDATE dashboards SET {', '.join(sets)} WHERE id = ?", params)
            conn.commit()
            return self.get(doc_id)
        finally:
            conn.close()

    def delete(self, doc_id: str) -> bool:
        conn = _get_db()
        try:
            r = conn.execute("DELETE FROM dashboards WHERE id = ?", (doc_id,))
            conn.commit()
            return r.rowcount > 0
        finally:
            conn.close()


dashboard_repo = DashboardRepository()
