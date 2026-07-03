from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlite3
from pathlib import Path

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
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS dashboards (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                original_query TEXT NOT NULL,
                chart_config TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                is_public INTEGER DEFAULT 0,
                is_favorite INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_dashboards_owner ON dashboards(owner_id);

            CREATE TABLE IF NOT EXISTS query_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                chart_type TEXT,
                status TEXT NOT NULL DEFAULT 'success',
                error_code TEXT,
                execution_time_ms INTEGER,
                saved_as_dashboard_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_history_user ON query_history(user_id);
            CREATE INDEX IF NOT EXISTS idx_history_created ON query_history(created_at);

            CREATE TABLE IF NOT EXISTS dashboard_feedback (
                id TEXT PRIMARY KEY,
                dashboard_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                rating TEXT NOT NULL,
                comment TEXT DEFAULT '',
                issue_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_feedback_dashboard ON dashboard_feedback(dashboard_id);
        """)
        conn.commit()
    finally:
        conn.close()
