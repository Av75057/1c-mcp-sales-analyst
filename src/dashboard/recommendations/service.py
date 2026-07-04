from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from src.dashboard.composite.service import _get_db
from src.dashboard.llm_service import generate_chart_config
from src.logger import logger


class RecommendationService:
    def generate(self, dashboard_id: str, dashboard_data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        try:
            insights = self._analyze_dashboard(dashboard_data or {})
            for insight in insights:
                rec = self._save(dashboard_id=dashboard_id, **insight)
                recommendations.append(rec)
        except Exception as e:
            logger.warning("[Recommendations] Failed to generate for {}: {}", dashboard_id, e)
        return recommendations

    def _analyze_dashboard(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []
        charts = data.get("charts", [])
        chart_types = {c.get("chart_config", {}).get("chart_type") for c in charts}

        if "pie" not in chart_types and len(charts) >= 2:
            insights.append({
                "title": "Добавьте круговую диаграмму",
                "description": "Для отображения структуры продаж по категориям",
                "confidence": 0.6,
                "reason": "В текущей панели нет круговых диаграмм, хотя они эффективны для показа долей",
                "suggested_action": "Добавить chart_type=pie с группировкой по Номенклатура.Группа",
            })

        if "line" not in chart_types and len(charts) >= 1:
            insights.append({
                "title": "Добавьте график динамики",
                "description": "Временной ряд продаж для отслеживания трендов",
                "confidence": 0.7,
                "reason": "Линейные графики помогают выявлять сезонность и тренды",
                "suggested_action": "Добавить chart_type=line с осью X по датам",
            })

        total_charts = len(charts)
        if total_charts == 1:
            insights.append({
                "title": "Расширьте панель метриками",
                "description": "Добавьте больше графиков для комплексного анализа",
                "confidence": 0.5,
                "reason": "Один график даёт ограниченное представление о данных",
                "suggested_action": "Добавить 2-3 графика разных типов",
            })

        if not insights:
            insights.append({
                "title": "Панель выглядит хорошо",
                "description": "Хороший набор визуализаций для анализа",
                "confidence": 0.8,
                "reason": "Разнообразие типов графиков покрывает основные потребности",
                "suggested_action": "Настройте автообновление для актуальности данных",
            })

        return insights

    def _save(self, dashboard_id: str, title: str, description: str, confidence: float, reason: str, suggested_action: str) -> dict[str, Any]:
        conn = _get_db()
        rid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            conn.execute(
                "INSERT INTO dashboard_recommendations (id, dashboard_id, title, description, confidence, reason, suggested_action, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (rid, dashboard_id, title, description, confidence, reason, suggested_action, now),
            )
            conn.commit()
            return {"id": rid, "title": title, "description": description, "confidence": confidence, "reason": reason, "suggested_action": suggested_action, "created_at": now}
        finally:
            conn.close()

    def list(self, dashboard_id: str) -> list[dict[str, Any]]:
        conn = _get_db()
        try:
            rows = conn.execute("SELECT * FROM dashboard_recommendations WHERE dashboard_id = ? ORDER BY confidence DESC, created_at DESC", (dashboard_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def mark_applied(self, rid: str) -> bool:
        conn = _get_db()
        try:
            r = conn.execute("UPDATE dashboard_recommendations SET is_applied = 1 WHERE id = ?", (rid,))
            conn.commit()
            return r.rowcount > 0
        finally:
            conn.close()


recommendation_service = RecommendationService()
