from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.logger import logger

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "dashboards.db"


class QueryCache:
    """Кэш результатов запросов к 1С. TTL по умолчанию 15 минут."""

    def __init__(self, db_path: str | None = None, ttl_seconds: int = 900):
        self.db_path = db_path or str(DB_PATH)
        self.ttl = timedelta(seconds=ttl_seconds)
        self._init_db()

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_cache (
                    cache_key TEXT PRIMARY KEY,
                    entity TEXT NOT NULL,
                    data TEXT NOT NULL,
                    row_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    hit_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_qc_expires ON query_cache(expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_qc_entity ON query_cache(entity)")
            conn.commit()
        finally:
            conn.close()

    def _make_key(self, chart_config: dict[str, Any]) -> str:
        normalized = json.dumps(chart_config, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, chart_config: dict[str, Any]) -> list[dict[str, Any]] | None:
        key = self._make_key(chart_config)
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT data, expires_at, hit_count FROM query_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
            if not row:
                return None
            expires_at = datetime.fromisoformat(row["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                conn.execute("DELETE FROM query_cache WHERE cache_key = ?", (key,))
                conn.commit()
                return None
            conn.execute("UPDATE query_cache SET hit_count = hit_count + 1 WHERE cache_key = ?", (key,))
            conn.commit()
            return json.loads(row["data"])
        finally:
            conn.close()

    def set(self, chart_config: dict[str, Any], data: list[dict[str, Any]]) -> None:
        key = self._make_key(chart_config)
        entity = chart_config.get("onec_query", {}).get("entity", "")
        conn = self._connect()
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + self.ttl
            conn.execute(
                """INSERT OR REPLACE INTO query_cache (cache_key, entity, data, row_count, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (key, entity, json.dumps(data, ensure_ascii=False), len(data), now.isoformat(), expires_at.isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def invalidate(self, entity: str | None = None) -> None:
        conn = self._connect()
        try:
            if entity:
                conn.execute("DELETE FROM query_cache WHERE entity = ?", (entity,))
            else:
                conn.execute("DELETE FROM query_cache")
            conn.commit()
        finally:
            conn.close()

    def stats(self) -> dict[str, Any]:
        conn = self._connect()
        try:
            total = conn.execute("SELECT COUNT(*) FROM query_cache").fetchone()[0]
            total_hits = conn.execute("SELECT COALESCE(SUM(hit_count), 0) FROM query_cache").fetchone()[0]
            expired = conn.execute("SELECT COUNT(*) FROM query_cache WHERE expires_at < ?", (datetime.now(timezone.utc).isoformat(),)).fetchone()[0]
            return {"entries": total, "total_hits": total_hits, "expired": expired, "active": total - expired}
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn


query_cache = QueryCache()
