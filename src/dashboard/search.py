from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.logger import logger

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "dashboards.db"


class DashboardSearch:
    """Полнотекстовый поиск по дашбордам через FTS5."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(DB_PATH)
        self._init_db()

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS dashboards_fts USING fts5(
                    dashboard_id UNINDEXED,
                    title,
                    description,
                    tags,
                    tokenize='unicode61'
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def index(self, dashboard_id: str, title: str, description: str, tags: list[str]) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO dashboards_fts (dashboard_id, title, description, tags) VALUES (?, ?, ?, ?)",
                (dashboard_id, title, description or "", " ".join(tags)),
            )
            conn.commit()
        finally:
            conn.close()

    def remove(self, dashboard_id: str) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM dashboards_fts WHERE dashboard_id = ?", (dashboard_id,))
            conn.commit()
        finally:
            conn.close()

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        if not query or not query.strip():
            return []
        conn = self._connect()
        try:
            rows = conn.execute(
                """SELECT dashboard_id, title, description, tags, rank
                   FROM dashboards_fts
                   WHERE dashboards_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def rebuild(self) -> None:
        """Перестроить FTS-индекс из таблицы dashboards."""
        conn = self._connect()
        try:
            conn.execute("DELETE FROM dashboards_fts")
            rows = conn.execute(
                "SELECT id, title, COALESCE(description, '') as descr, COALESCE(tags, '[]') as t FROM dashboards WHERE deleted_at IS NULL"
            ).fetchall()
            for r in rows:
                tags = json.loads(r["t"]) if isinstance(r["t"], str) else []
                conn.execute(
                    "INSERT INTO dashboards_fts (dashboard_id, title, description, tags) VALUES (?, ?, ?, ?)",
                    (r["id"], r["title"], r["descr"], " ".join(tags)),
                )
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn


dashboard_search = DashboardSearch()
