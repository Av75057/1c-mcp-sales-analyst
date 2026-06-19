from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from src.logger import logger
from src.whatif.engine.data_loader import DataLoader
from src.whatif.models import (
    DataQuality,
    FinancialEffect,
    Risk,
    ScenarioMetrics,
    SimulationRequest,
    SimulationResult,
    TimeSeries,
)
from src.whatif.models.elasticity_model import ElasticityModel
from src.whatif.scenarios.base import BaseScenarioHandler


class PriceChangeScenario(BaseScenarioHandler):
    async def execute(self, request: SimulationRequest) -> SimulationResult:
        logger.info("PriceChange: {} | change={}% | days={}", request.entity_name, request.parameters.get("change_percent"), request.parameters.get("period_days", 30))

        loader = DataLoader()
        change_pct = request.parameters.get("change_percent", 10)
        period_days = request.parameters.get("period_days", 30)

        sales = await loader.get_sales_history(
            entity_type=request.entity_type,
            entity_name=request.entity_name,
            period_months=12,
        )

        if not sales:
            return SimulationResult(
                request=request,
                confidence=0.0,
                recommendations=["Недостаточно данных для симуляции"],
            )

        # Считаем базовые метрики
        recent = [s for s in sales if s.get("date", "")[:10] >= (date.today() - timedelta(days=period_days)).isoformat()]
        baseline_volume = sum(s.get("quantity", 0) for s in (recent or sales))
        baseline_revenue = sum(s.get("sum", 0) for s in (recent or sales))
        baseline_avg_price = baseline_revenue / baseline_volume if baseline_volume > 0 else 0
        baseline_margin = baseline_revenue * 0.4

        # Эластичность
        model = ElasticityModel()
        model.train(sales, entity_id=request.entity_name)
        prediction = model.predict(change_pct, baseline_volume, baseline_avg_price)

        projected_volume = prediction["new_volume"]
        projected_price = prediction["new_price"]
        projected_revenue = prediction["new_revenue"]
        projected_margin = projected_revenue * 0.4

        # Monte-Carlo (упрощённо)
        np.random.seed(42)
        vol_changes = np.random.normal(prediction["volume_change_percent"] / 100, abs(model.elasticity * 0.3), 1000)
        revenues = baseline_volume * (1 + vol_changes) * projected_price
        rev_low = float(np.percentile(revenues, 10))
        rev_high = float(np.percentile(revenues, 90))

        # Time series
        dates = [(date.today() + timedelta(days=i)).isoformat() for i in range(period_days)]
        daily_base = baseline_volume / period_days
        daily_new = projected_volume / period_days
        ts = TimeSeries(
            dates=dates,
            baseline=[daily_base * (1 + 0.02 * np.sin(i * 0.2)) for i in range(period_days)],
            projected=[daily_new * (1 + 0.02 * np.sin(i * 0.2)) for i in range(period_days)],
            projected_low=[rev_low / period_days] * period_days,
            projected_high=[rev_high / period_days] * period_days,
        )

        confidence = min(0.9, 0.3 + model.r2_score * 0.5 + min(len(sales) / 100, 0.2))

        delta_volume = projected_volume - baseline_volume
        delta_revenue = projected_revenue - baseline_revenue
        delta_margin = projected_margin - baseline_margin

        risks = [
            Risk(name="Отток клиентов из-за роста цен", probability=min(1.0, max(0.0, abs(model.elasticity) * change_pct / 50)), impact="Снижение объёма продаж", mitigation="Предупредить ключевых клиентов заранее"),
            Risk(name="Реакция конкурентов", probability=0.3, impact="Потеря доли рынка", mitigation="Мониторить цены конкурентов"),
        ]

        recommendations = []
        if change_pct > 0:
            if delta_revenue > 0:
                recommendations.append(f"Поднятие цены на {change_pct}% выгодно: выручка вырастет на {delta_revenue:,.0f} ₽")
            else:
                recommendations.append(f"Поднятие цены на {change_pct}% НЕ выгодно: выручка упадёт на {abs(delta_revenue):,.0f} ₽")
            if abs(model.elasticity) < 0.8:
                recommendations.append("Спрос неэластичный — можно поднимать цену без значительной потери объёма")
            else:
                recommendations.append("Спрос эластичный — рекомендуется поднимать цену не более чем на 5%")
            recommendations.append("Мониторить продажи первые 2 недели после изменения")

        return SimulationResult(
            request=request,
            baseline=ScenarioMetrics(revenue=baseline_revenue, margin=baseline_margin, volume=baseline_volume, avg_price=baseline_avg_price),
            projected=ScenarioMetrics(revenue=projected_revenue, margin=projected_margin, volume=projected_volume, avg_price=projected_price),
            delta=ScenarioMetrics(revenue=delta_revenue, margin=delta_margin, volume=delta_volume, avg_price=projected_price - baseline_avg_price),
            financial_effect=FinancialEffect(additional_revenue=delta_revenue, additional_margin=delta_margin),
            risks=risks,
            recommendations=recommendations,
            confidence=round(confidence, 2),
            confidence_interval={"revenue_low": round(rev_low, 2), "revenue_high": round(rev_high, 2)},
            time_series=ts,
            data_quality=DataQuality(history_months=12, data_points=len(sales), model_used="RidgeRegression"),
        )
