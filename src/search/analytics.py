from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ANALYTICS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "search_queries.jsonl"


def log_query(
    user_id: str,
    query: str,
    filters: dict[str, Any] | None = None,
    results_count: int = 0,
    search_time_ms: float = 0.0,
    strategy: str = "hybrid",
) -> None:
    """Логирует поисковый запрос в JSONL файл."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "query": query,
        "filters": filters or {},
        "results_count": results_count,
        "search_time_ms": round(search_time_ms, 2),
        "strategy": strategy,
    }
    ANALYTICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ANALYTICS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _read(limit: int = 10000) -> list[dict[str, Any]]:
    if not ANALYTICS_FILE.exists():
        return []
    try:
        lines = ANALYTICS_FILE.read_text(encoding="utf-8").strip().split("\n")
        result = []
        for line in lines:
            if line.strip():
                try:
                    result.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return result[-limit:]
    except Exception:
        return []


def top_queries(days: int = 7, limit: int = 20) -> list[dict[str, Any]]:
    logs = _read()
    cutoff = time.time() - days * 86400
    counts: dict[str, int] = defaultdict(int)
    time_ms: dict[str, float] = defaultdict(float)
    for entry in logs:
        try:
            ts = datetime.fromisoformat(entry.get("timestamp", "")).timestamp()
        except (ValueError, TypeError):
            ts = 0
        if ts < cutoff:
            continue
        q = entry.get("query", "")
        counts[q] += 1
        time_ms[q] += entry.get("search_time_ms", 0)
    result = [{"query": q, "count": c, "avg_time_ms": round(time_ms[q] / c, 1)} for q, c in sorted(counts.items(), key=lambda x: -x[1])[:limit]]
    return result


def no_results_queries(days: int = 7, limit: int = 20) -> list[dict[str, Any]]:
    logs = _read()
    cutoff = time.time() - days * 86400
    counts: dict[str, int] = defaultdict(int)
    for entry in logs:
        try:
            ts = datetime.fromisoformat(entry.get("timestamp", "")).timestamp()
        except (ValueError, TypeError):
            ts = 0
        if ts < cutoff:
            continue
        if entry.get("results_count", 0) == 0:
            counts[entry.get("query", "")] += 1
    return [{"query": q, "count": c} for q, c in sorted(counts.items(), key=lambda x: -x[1])[:limit]]


def total_count(days: int = 7) -> int:
    logs = _read()
    cutoff = time.time() - days * 86400
    count = 0
    for entry in logs:
        try:
            ts = datetime.fromisoformat(entry.get("timestamp", "")).timestamp()
        except (ValueError, TypeError):
            ts = 0
        if ts >= cutoff:
            count += 1
    return count
