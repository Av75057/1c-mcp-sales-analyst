from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.logger import logger

LINEAGE_DB_URL = "sqlite+aiosqlite:///data/data_lineage.db"


class LineageTracker:
    def __init__(self) -> None:
        self._engine = create_async_engine(LINEAGE_DB_URL, echo=False)
        self._session_factory = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    async def init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS data_lineage (
                    id TEXT PRIMARY KEY,
                    source_system TEXT NOT NULL,
                    source_endpoint TEXT NOT NULL,
                    query_hash TEXT NOT NULL,
                    data_hash TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    validation_status TEXT NOT NULL,
                    validation_issues TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_by TEXT
                )
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lineage_endpoint ON data_lineage(source_endpoint)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lineage_created ON data_lineage(created_at)"))

    async def track(
        self,
        source_system: str,
        source_endpoint: str,
        query_params: dict[str, Any],
        data: list[dict[str, Any]],
        validation_status: str = "valid",
        validation_issues: list[dict[str, Any]] | None = None,
        created_by: str = "system",
    ) -> str:
        entry_id = str(uuid.uuid4())
        qh = hashlib.md5(json.dumps(query_params, sort_keys=True, default=str).encode()).hexdigest()[:16]
        dh = hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:16]
        now = datetime.utcnow()

        async with self._session_factory() as db:
            await db.execute(
                text("INSERT INTO data_lineage (id, source_system, source_endpoint, query_hash, data_hash, row_count, validation_status, validation_issues, created_at, expires_at, created_by) VALUES (:id, :ss, :se, :qh, :dh, :rc, :vs, :vi, :ca, :ea, :cb)"),
                {"id": entry_id, "ss": source_system, "se": source_endpoint, "qh": qh, "dh": dh, "rc": len(data), "vs": validation_status, "vi": json.dumps(validation_issues or [], ensure_ascii=False), "ca": now, "ea": now + timedelta(hours=1), "cb": created_by},
            )
            await db.commit()
        return entry_id

    async def get_lineage(self, source_endpoint: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        async with self._session_factory() as db:
            if source_endpoint:
                rows = await db.execute(text("SELECT * FROM data_lineage WHERE source_endpoint = :se ORDER BY created_at DESC LIMIT :lim"), {"se": source_endpoint, "lim": limit})
            else:
                rows = await db.execute(text("SELECT * FROM data_lineage ORDER BY created_at DESC LIMIT :lim"), {"lim": limit})
            return [dict(r._mapping) for r in rows]

    async def cleanup(self, days_old: int = 30) -> int:
        async with self._session_factory() as db:
            r = await db.execute(text("DELETE FROM data_lineage WHERE created_at < :cutoff"), {"cutoff": datetime.utcnow() - timedelta(days=days_old)})
            await db.commit()
            return r.rowcount


lineage_tracker = LineageTracker()
