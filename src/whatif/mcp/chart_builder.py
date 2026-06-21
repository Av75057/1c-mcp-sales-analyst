from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.whatif.scenarios.base import ScenarioResult


class WhatIfChartBuilder:
    def build_chart_params(self, result: ScenarioResult) -> dict[str, Any]:
        if result.scenario_type == "price_change":
            return self._price_change(result)
        elif result.scenario_type == "promotion":
            return self._promotion(result)
        elif result.scenario_type == "purchase_change":
            return self._purchase(result)
        elif result.scenario_type == "employee_departure":
            return self._employee(result)
        raise ValueError(f"Неизвестный сценарий: {result.scenario_type}")

    def _price_change(self, r: ScenarioResult) -> dict[str, Any]:
        days = r.additional_data.get("period_days", 30)
        labels = [f"День {i+1}" for i in range(days)]
        b = r.baseline_metrics.get("daily_revenue", r.baseline_metrics.get("revenue", 0)) / days
        p = r.projected_metrics.get("daily_revenue", r.projected_metrics.get("revenue", 0)) / days
        np.random.seed(42)
        bs = [b * (1 + np.random.normal(0, 0.03)) for _ in range(days)]
        ps = [p * (1 + np.random.normal(0, 0.03)) for _ in range(days)]
        return {"chart_type": "line", "title": f"Прогноз: {r.scenario_name}", "x_data": labels, "y_data": [bs, ps], "series_names": ["Без изменений", "С изменениями"], "x_label": "День", "y_label": "Выручка, ₽", "color_scheme": "corporate"}

    def _promotion(self, r: ScenarioResult) -> dict[str, Any]:
        days = r.additional_data.get("period_days", 30)
        labels = [f"День {i+1}" for i in range(days)]
        b = r.baseline_metrics.get("daily_revenue", r.baseline_metrics.get("revenue", 0)) / days
        p = r.projected_metrics.get("daily_revenue", r.projected_metrics.get("revenue", 0)) / days
        return {"chart_type": "line", "title": f"Эффект акции: {r.scenario_name}", "x_data": labels, "y_data": [[b] * days, [p] * days], "series_names": ["Без акции", "С акцией"], "x_label": "День", "y_label": "Выручка, ₽", "color_scheme": "vibrant"}

    def _purchase(self, r: ScenarioResult) -> dict[str, Any]:
        cats = ["Запас (дни)", "Stock-out риск (%)", "Заморожено (тыс ₽)"]
        bv = [r.baseline_metrics.get("days_of_stock", 0), r.baseline_metrics.get("stockout_prob", 0) * 100, r.baseline_metrics.get("frozen_money", 0) / 1000]
        pv = [r.projected_metrics.get("days_of_stock", 0), r.projected_metrics.get("stockout_prob", 0) * 100, r.projected_metrics.get("frozen_money", 0) / 1000]
        return {"chart_type": "bar", "title": f"Сравнение: {r.scenario_name}", "x_data": cats, "y_data": [bv, pv], "series_names": ["Сейчас", "Станет"], "x_label": "Показатель", "y_label": "Значение", "color_scheme": "corporate"}

    def _employee(self, r: ScenarioResult) -> dict[str, Any]:
        cats = ["Пессимистичный", "Реалистичный", "Оптимистичный"]
        vals = [r.projected_metrics.get("pessimistic_loss_3m", 0) / 1_000_000, r.projected_metrics.get("realistic_loss_3m", 0) / 1_000_000, r.projected_metrics.get("optimistic_loss_3m", 0) / 1_000_000]
        return {"chart_type": "bar", "title": f"Прогноз потерь: {r.entity_name}", "x_data": cats, "y_data": vals, "x_label": "Сценарий", "y_label": "Потеря выручки, млн ₽", "color_scheme": "vibrant"}
