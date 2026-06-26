from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

import sqlite3
from pathlib import Path

from src.rag.models import KnowledgeDocument

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge.db"


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
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                document_type TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL DEFAULT 'system',
                is_active INTEGER DEFAULT 1,
                version INTEGER DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_documents(document_type);
            CREATE INDEX IF NOT EXISTS idx_knowledge_active ON knowledge_documents(is_active);
        """)
        conn.commit()
    finally:
        conn.close()


def create_doc(title: str, content: str, doc_type: str = "general", tags: list[str] | None = None, created_by: str = "system") -> dict[str, Any]:
    conn = _get_db()
    doc_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    try:
        conn.execute(
            "INSERT INTO knowledge_documents (id, title, content, document_type, tags, created_at, updated_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (doc_id, title, content, doc_type, json.dumps(tags or []), now, now, created_by),
        )
        conn.commit()
        return {"id": doc_id, "title": title, "content": content, "document_type": doc_type, "tags": tags or [], "created_at": now}
    finally:
        conn.close()


def list_docs(doc_type: str | None = None, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    conn = _get_db()
    try:
        if doc_type:
            rows = conn.execute("SELECT * FROM knowledge_documents WHERE document_type = ? AND is_active = 1 ORDER BY created_at DESC LIMIT ? OFFSET ?", (doc_type, limit, offset)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM knowledge_documents WHERE is_active = 1 ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_doc(doc_id: str) -> dict[str, Any] | None:
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM knowledge_documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_doc(doc_id: str, title: str | None = None, content: str | None = None, tags: list[str] | None = None) -> bool:
    conn = _get_db()
    now = datetime.utcnow().isoformat()
    try:
        updates = []
        params: list[Any] = []
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))
        if not updates:
            return False
        updates.append("version = version + 1")
        updates.append("updated_at = ?")
        params.append(now)
        params.append(doc_id)
        r = conn.execute(f"UPDATE knowledge_documents SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        return r.rowcount > 0
    finally:
        conn.close()


def delete_doc(doc_id: str) -> bool:
    conn = _get_db()
    try:
        r = conn.execute("UPDATE knowledge_documents SET is_active = 0 WHERE id = ?", (doc_id,))
        conn.commit()
        return r.rowcount > 0
    finally:
        conn.close()


def search_docs(query: str, limit: int = 10) -> list[dict[str, Any]]:
    conn = _get_db()
    try:
        rows = conn.execute("SELECT * FROM knowledge_documents WHERE is_active = 1").fetchall()
        q = query.lower()
        scored = []
        for r in rows:
            d = dict(r)
            title = (d.get("title") or "").lower()
            content = (d.get("content") or "").lower()
            tags = (d.get("tags") or "").lower()
            score = 0
            if q in title:
                score += 10
            if q in content:
                score += 3
            if q in tags:
                score += 5
            if score > 0:
                d["relevance"] = score
                scored.append(d)
        scored.sort(key=lambda x: -x["relevance"])
        return scored[:limit]
    finally:
        conn.close()


def get_stats() -> dict[str, Any]:
    conn = _get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM knowledge_documents WHERE is_active = 1").fetchone()[0]
        by_type = conn.execute("SELECT document_type, COUNT(*) as cnt FROM knowledge_documents WHERE is_active = 1 GROUP BY document_type").fetchall()
        return {"total_documents": total, "by_type": {r["document_type"]: r["cnt"] for r in by_type}}
    finally:
        conn.close()
