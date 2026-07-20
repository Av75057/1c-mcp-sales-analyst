from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

from src.logger import logger

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "nomenclature_cache.db"


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    return conn


def init() -> None:
    """Создаёт FTS5 таблицу, если её нет."""
    conn = _get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS nomenclature (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                article TEXT DEFAULT '',
                barcode TEXT DEFAULT '',
                group_name TEXT DEFAULT '',
                item_type TEXT DEFAULT '',
                price REAL DEFAULT 0,
                stock_qty REAL DEFAULT 0,
                description TEXT DEFAULT '',
                updated_at REAL DEFAULT 0
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS nomenclature_fts USING fts5(
                name, article, barcode, description,
                content='nomenclature',
                content_rowid='rowid',
                tokenize='unicode61'
            );

            CREATE TRIGGER IF NOT EXISTS nomenclature_ai AFTER INSERT ON nomenclature BEGIN
                INSERT INTO nomenclature_fts(rowid, name, article, barcode, description)
                VALUES (new.rowid, new.name, new.article, new.barcode, new.description);
            END;

            CREATE TRIGGER IF NOT EXISTS nomenclature_ad AFTER DELETE ON nomenclature BEGIN
                INSERT INTO nomenclature_fts(nomenclature_fts, rowid, name, article, barcode, description)
                VALUES('delete', old.rowid, old.name, old.article, old.barcode, old.description);
            END;

            CREATE TRIGGER IF NOT EXISTS nomenclature_au AFTER UPDATE ON nomenclature BEGIN
                INSERT INTO nomenclature_fts(nomenclature_fts, rowid, name, article, barcode, description)
                VALUES('delete', old.rowid, old.name, old.article, old.barcode, old.description);
                INSERT INTO nomenclature_fts(rowid, name, article, barcode, description)
                VALUES (new.rowid, new.name, new.article, new.barcode, new.description);
            END;

            CREATE INDEX IF NOT EXISTS idx_nomenclature_updated ON nomenclature(updated_at);
        """)
        conn.commit()
    finally:
        conn.close()


def needs_refresh(max_age: int = 3600) -> bool:
    """Проверяет, нужно ли обновить кэш."""
    conn = _get_db()
    try:
        row = conn.execute("SELECT COUNT(*) FROM nomenclature").fetchone()
        if row[0] == 0:
            return True
        row = conn.execute("SELECT MAX(updated_at) FROM nomenclature").fetchone()
        return (row[0] or 0) < time.time() - max_age
    finally:
        conn.close()


def refresh(items: list[dict[str, Any]]) -> int:
    """Заполняет/обновляет кэш номенклатуры."""
    conn = _get_db()
    now = time.time()
    count = 0
    try:
        conn.execute("DELETE FROM nomenclature")
        conn.execute("DELETE FROM nomenclature_fts")
        for item in items:
            ref = item.get("ref", item.get("id", str(count)))
            article = item.get("article", item.get("code", ""))
            if not article or article == ref:
                article = item.get("article", "")
            conn.execute(
                "INSERT OR REPLACE INTO nomenclature (id, name, article, barcode, group_name, item_type, price, stock_qty, description, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ref,
                    item.get("name", ""),
                    article,
                    item.get("barcode", ""),
                    item.get("group", item.get("item_type", "")),
                    item.get("item_type", ""),
                    item.get("price", 0.0),
                    item.get("stock_qty", 0.0),
                    item.get("description", ""),
                    now,
                ),
            )
            count += 1
        conn.commit()
        logger.info("FTS cache refreshed: {} items", count)
    finally:
        conn.close()
    return count


async def ensure_fresh(max_age: int = 3600) -> bool:
    """Проверяет и при необходимости обновляет кэш."""
    if not needs_refresh(max_age):
        return True
    try:
        from src.tools import get_client

        client = get_client()
        # Build nomenclature from stock + sales data (which we can always fetch)
        items: list[dict[str, Any]] = []

        # Get stock items for names
        try:
            stock_items = await client.get_stock()
            seen = set()
            for s in stock_items:
                name = s.get("nomenclature", "")
                qty = s.get("quantity", 0)
                if name and name not in seen:
                    seen.add(name)
                    items.append({"name": name, "stock_qty": float(qty), "ref": name, "article": ""})
        except Exception as e:
            logger.warning("Stock fetch failed: {}", e)

        # Enrich with price data from sales
        try:
            from datetime import date, timedelta
            sales = await client.get_sales(
                date_from=(date.today() - timedelta(days=90)).isoformat(),
                date_to=date.today().isoformat(),
            )
            price_by_name: dict[str, float] = {}
            for s in sales:
                name = s.get("nomenclature", "")
                sprice = s.get("sum", 0)
                sqty = s.get("quantity", 0)
                if name and float(sqty) > 0:
                    price_by_name[name] = float(sprice) / float(sqty)
            for item in items:
                name = item.get("name", "")
                if name in price_by_name:
                    item["price"] = round(price_by_name[name], 2)
        except Exception as e:
            logger.warning("Price enrichment failed: {}", e)

        if items:
            refresh(items)
            return True
        return False
    except Exception as e:
        logger.warning("FTS cache refresh failed: {}", e)
        return False


def _escape_fts(query: str) -> str:
    """Экранирует спецсимволы FTS5 и строит безопасный запрос."""
    import re

    # Remove FTS5 operators and wrap each word in quotes to force literal search
    words = re.findall(r"[^\s\"'()*\\-]+", query)
    if not words:
        return f'"{query}"'
    return " AND ".join(f'"{w}"' for w in words)


def search(query: str, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """FTS5 поиск с BM25 ранжированием."""
    conn = _get_db()
    try:
        safe = _escape_fts(query)

        sql = """
            SELECT n.id, n.name, n.article, n.barcode, n.group_name, n.item_type, n.price, n.stock_qty,
                   bm25(nomenclature_fts, 10.0, 8.0, 10.0, 3.0) as rank
            FROM nomenclature_fts
            JOIN nomenclature n ON n.rowid = nomenclature_fts.rowid
            WHERE nomenclature_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(sql, (safe, limit, offset)).fetchall()
        if not rows:
            # Try prefix search
            safe_prefix = " ".join(f'"{w}"*' for w in query.split() if w.strip("'\""))
            if safe_prefix != safe:
                rows = conn.execute(sql, (safe_prefix, limit, offset)).fetchall()

        results = []
        for row in rows:
            rank = row[8] or 0.0
            # Normalize BM25 score: lower is better, map to 1.0-0.0 range
            score = max(0.0, min(1.0, 1.0 - (rank / 50.0)))
            results.append({
                "id": row[0],
                "name": row[1],
                "article": row[2] or "",
                "barcode": row[3] or "",
                "group": row[4] or "",
                "item_type": row[5] or "",
                "price": row[6] or 0.0,
                "stock_qty": row[7] or 0.0,
                "score": score,
            })
        return results
    finally:
        conn.close()


def search_count(query: str) -> int:
    """Количество результатов FTS5 поиска."""
    conn = _get_db()
    try:
        safe = query.replace("'", "''")
        row = conn.execute(
            "SELECT COUNT(*) FROM nomenclature_fts WHERE nomenclature_fts MATCH ?",
            (safe,),
        ).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()
