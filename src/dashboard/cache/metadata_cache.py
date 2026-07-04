from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.logger import logger

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "dashboards.db"


class MetadataCache:
    """Кэш метаданных 1С (сущности и их поля). TTL по умолчанию 1 час."""

    def __init__(self, db_path: str | None = None, ttl_hours: int = 1):
        self.db_path = db_path or str(DB_PATH)
        self.ttl = timedelta(hours=ttl_hours)
        self._init_db()

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata_cache (
                    entity TEXT PRIMARY KEY,
                    fields TEXT NOT NULL,
                    relationships TEXT,
                    fetched_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def get(self, entity: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT fields, relationships, expires_at FROM metadata_cache WHERE entity = ?",
                (entity,),
            ).fetchone()
            if not row:
                return None
            expires_at = datetime.fromisoformat(row["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                conn.execute("DELETE FROM metadata_cache WHERE entity = ?", (entity,))
                conn.commit()
                return None
            return {
                "fields": json.loads(row["fields"]),
                "relationships": json.loads(row["relationships"]) if row["relationships"] else {},
            }
        finally:
            conn.close()

    def set(self, entity: str, fields: list[str], relationships: dict | None = None) -> None:
        conn = self._connect()
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + self.ttl
            conn.execute(
                """INSERT OR REPLACE INTO metadata_cache (entity, fields, relationships, fetched_at, expires_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (entity, json.dumps(fields, ensure_ascii=False), json.dumps(relationships or {}, ensure_ascii=False), now.isoformat(), expires_at.isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def invalidate(self, entity: str | None = None) -> None:
        conn = self._connect()
        try:
            if entity:
                conn.execute("DELETE FROM metadata_cache WHERE entity = ?", (entity,))
            else:
                conn.execute("DELETE FROM metadata_cache")
            conn.commit()
        finally:
            conn.close()

    def stats(self) -> dict[str, Any]:
        conn = self._connect()
        try:
            total = conn.execute("SELECT COUNT(*) FROM metadata_cache").fetchone()[0]
            expired = conn.execute("SELECT COUNT(*) FROM metadata_cache WHERE expires_at < ?", (datetime.now(timezone.utc).isoformat(),)).fetchone()[0]
            return {"total": total, "expired": expired, "active": total - expired}
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn


metadata_cache = MetadataCache()
