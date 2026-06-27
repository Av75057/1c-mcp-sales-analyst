from __future__ import annotations

import hashlib
import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.anonymization.models import SensitiveDataType

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "anonymization.db"

TOKEN_PATTERN = re.compile(r"\[(ПЕРС|ОРГ|КОНТ|ФИН|ДОК|АДР|КАСТ)-(\d+)\]")


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS anonymization_tokens (
                id TEXT PRIMARY KEY,
                token TEXT NOT NULL UNIQUE,
                original_value_hash TEXT NOT NULL,
                data_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                expires_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tokens_token ON anonymization_tokens(token);
            CREATE INDEX IF NOT EXISTS idx_tokens_user ON anonymization_tokens(user_id);
            CREATE TABLE IF NOT EXISTS anonymization_reveals (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT,
                tokens_count INTEGER NOT NULL,
                context_preview TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_reveals_user ON anonymization_reveals(user_id);
        """)
        conn.commit()
    finally:
        conn.close()


def _next_token(data_type: SensitiveDataType) -> str:
    conn = _get_db()
    try:
        prefix = data_type.value
        row = conn.execute("SELECT COUNT(*) as cnt FROM anonymization_tokens WHERE data_type = ?", (prefix,)).fetchone()
        num = (row["cnt"] if row else 0) + 1
        return f"[{prefix}-{num:05d}]"
    finally:
        conn.close()


def get_or_create_token(value: str, data_type: SensitiveDataType, user_id: str, session_id: str = "") -> str:
    conn = _get_db()
    try:
        value_hash = hashlib.sha256(value.encode()).hexdigest()[:16]
        existing = conn.execute("SELECT token FROM anonymization_tokens WHERE original_value_hash = ? AND data_type = ?", (value_hash, data_type.value)).fetchone()
        if existing:
            conn.execute("UPDATE anonymization_tokens SET last_accessed_at = CURRENT_TIMESTAMP, access_count = access_count + 1 WHERE token = ?", (existing["token"],))
            conn.commit()
            return existing["token"]
        token = _next_token(data_type)
        conn.execute(
            "INSERT INTO anonymization_tokens (id, token, original_value_hash, data_type, user_id, session_id, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), token, value_hash, data_type.value, user_id, session_id, (datetime.utcnow() + timedelta(days=90)).isoformat()),
        )
        conn.commit()
        return token
    finally:
        conn.close()


def reveal_text(text: str, user_id: str, session_id: str = "") -> str:
    conn = _get_db()
    try:
        tokens_found = TOKEN_PATTERN.findall(text)
        if not tokens_found:
            return text
        result = text
        count = 0
        for prefix, num in tokens_found:
            token = f"[{prefix}-{num}]"
            row = conn.execute("SELECT original_value_hash FROM anonymization_tokens WHERE token = ?", (token,)).fetchone()
            if row:
                result = result.replace(token, f"[{prefix}-{num}:hidden]")
                count += 1
        conn.execute(
            "INSERT INTO anonymization_reveals (id, user_id, session_id, tokens_count, context_preview) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, session_id, count, text[:200]),
        )
        conn.commit()
        return result
    finally:
        conn.close()


def get_stats() -> dict[str, Any]:
    conn = _get_db()
    try:
        total = conn.execute("SELECT COUNT(*) as cnt FROM anonymization_tokens").fetchone()["cnt"]
        by_type = conn.execute("SELECT data_type, COUNT(*) as cnt FROM anonymization_tokens GROUP BY data_type").fetchall()
        reveals = conn.execute("SELECT COUNT(*) as cnt FROM anonymization_reveals WHERE created_at > datetime('now', '-1 day')").fetchone()["cnt"]
        return {"total_tokens": total, "by_type": {r["data_type"]: r["cnt"] for r in by_type}, "reveals_today": reveals}
    finally:
        conn.close()
