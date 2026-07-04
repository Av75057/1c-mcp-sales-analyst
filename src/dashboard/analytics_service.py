from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "dashboards.db"


class DashboardAnalytics:
    """Аналитика использования дашбордов (для админов)."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(DB_PATH)

    def overview(self, days: int = 30) -> dict[str, Any]:
        conn = self._connect()
        try:
            since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            table = "composite_dashboards"

            total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            active = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE updated_at > ?", (since,)).fetchone()[0]
            total_views = conn.execute(f"SELECT COALESCE(SUM(view_count), 0) FROM {table}").fetchone()[0]
            total_shares = conn.execute("SELECT COUNT(*) FROM dashboard_shares WHERE is_active = 1").fetchone()[0]
            total_exports = conn.execute("SELECT value FROM dashboard_metrics WHERE metric = 'exports_total'").fetchone()
            total_exports = int(total_exports[0]) if total_exports else 0

            # Топ дашбордов
            top = conn.execute(
                f"SELECT id, title, view_count FROM {table} ORDER BY view_count DESC LIMIT 10"
            ).fetchall()

            # Топ тегов (хранятся как JSON-строка в поле tags)
            all_tags = conn.execute(f"SELECT tags FROM {table} WHERE tags IS NOT NULL AND tags != '[]'").fetchall()
            tag_counter: dict[str, int] = {}
            for row in all_tags:
                try:
                    for tag in json.loads(row["tags"]):
                        tag_counter[tag] = tag_counter.get(tag, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass
            top_tags = sorted(tag_counter.items(), key=lambda x: -x[1])[:20]

            # Типы графиков (из поля charts)
            all_charts = conn.execute(f"SELECT charts FROM {table}").fetchall()
            chart_counter: dict[str, int] = {}
            for row in all_charts:
                try:
                    for chart in json.loads(row["charts"]):
                        ct = chart.get("chart_config", {}).get("chart_type", "unknown")
                        chart_counter[ct] = chart_counter.get(ct, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass
            chart_types = sorted(chart_counter.items(), key=lambda x: -x[1])

            # Feedback summary
            try:
                fb_positive = conn.execute("SELECT COUNT(*) FROM dashboard_feedback WHERE rating = 'positive'").fetchone()[0]
                fb_negative = conn.execute("SELECT COUNT(*) FROM dashboard_feedback WHERE rating = 'negative'").fetchone()[0]
            except Exception:
                fb_positive = fb_negative = 0
            fb_total = fb_positive + fb_negative

            return {
                "period": {"from": since, "to": datetime.now(timezone.utc).isoformat()},
                "total_dashboards": total,
                "active_dashboards": active,
                "total_views": total_views,
                "total_shares": total_shares,
                "total_exports": total_exports,
                "top_dashboards": [dict(r) for r in top],
                "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
                "chart_types": [{"type": t, "count": c} for t, c in chart_types],
                "feedback_summary": {
                    "positive": fb_positive,
                    "negative": fb_negative,
                    "total": fb_total,
                    "satisfaction_rate": round(fb_positive / fb_total, 2) if fb_total > 0 else 0,
                },
            }
        finally:
            conn.close()

    def increment_exports(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                INSERT INTO dashboard_metrics (metric, value, updated_at)
                VALUES ('exports_total', 1, datetime('now'))
                ON CONFLICT(metric) DO UPDATE SET value = value + 1, updated_at = datetime('now')
            """)
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_metrics (
                metric TEXT PRIMARY KEY,
                value INTEGER DEFAULT 0,
                updated_at TEXT
            )
        """)
        return conn


dashboard_analytics = DashboardAnalytics()
