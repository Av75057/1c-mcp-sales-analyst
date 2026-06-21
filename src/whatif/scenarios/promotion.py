from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.logger import logger
from src.whatif.engine.financial_calculator import FinancialCalculator
from src.whatif.models.elasticity_model import ElasticityModel
from src.whatif.models.monte_carlo import MonteCarloSimulator
from src.whatif.scenarios.base import BaseScenario, ScenarioResult


@dataclass
class PromotionParams:
    entity_name: str = ""
    historical_data: pd.DataFrame = field(default_factory=pd.DataFrame)
    discount_percent: float = 0.0
    promotion_days: int = 14
    cost_per_unit: float = 0.0
    cannibalization_rate: float = 0.20
    new_customer_rate: float = 0.15
    retention_boost: float = 0.10


class PromotionScenario(BaseScenario):
    def __init__(self) -> None:
        super().__init__()
        self.scenario_type = "promotion"
        self.scenario_name = "Акция/Скидка"
        self.elasticity_model = ElasticityModel()
        self.mc_simulator = MonteCarloSimulator(iterations=1000)
        self.financial_calc = FinancialCalculator()

    def simulate(self, params: PromotionParams) -> ScenarioResult:
        logger.info("Promotion: {} | скидка {}% | {} дней", params.entity_name, params.discount_percent, params.promotion_days)

        elasticity_result = self.elasticity_model.fit(params.historical_data)
        elasticity_pred = self.elasticity_model.predict(-params.discount_percent)
        volume_boost_pct = elasticity_pred.volume_change_percent

        recent = params.historical_data.tail(30)
        baseline_price = float(recent["price"].mean())
        baseline_daily_vol = float(recent["quantity"].mean())
        baseline_daily_rev = baseline_price * baseline_daily_vol
        baseline_daily_margin = baseline_daily_rev - params.cost_per_unit * baseline_daily_vol

        promo_price = baseline_price * (1 - params.discount_percent / 100)
        promo_daily_vol = baseline_daily_vol * (1 + volume_boost_pct / 100)
        promo_daily_rev = promo_price * promo_daily_vol
        promo_daily_margin = promo_daily_rev - params.cost_per_unit * promo_daily_vol

        total_baseline_rev = baseline_daily_rev * params.promotion_days
        total_baseline_margin = baseline_daily_margin * params.promotion_days
        total_promo_rev = promo_daily_rev * params.promotion_days
        total_promo_margin = promo_daily_margin * params.promotion_days

        cannibalization_loss = total_promo_rev * params.cannibalization_rate
        net_promo_rev = total_promo_rev - cannibalization_loss
        margin_rate = total_promo_margin / total_promo_rev if total_promo_rev > 0 else 0
        net_promo_margin = total_promo_margin - cannibalization_loss * margin_rate

        new_customers_value = net_promo_rev * params.new_customer_rate
        retention_value = net_promo_rev * params.retention_boost
        long_term_benefit = new_customers_value + retention_value

        revenue_delta = net_promo_rev - total_baseline_rev
        margin_delta = net_promo_margin - total_baseline_margin
        revenue_delta_pct = (revenue_delta / total_baseline_rev * 100) if total_baseline_rev > 0 else 0
        margin_delta_pct = (margin_delta / total_baseline_margin * 100) if total_baseline_margin > 0 else 0

        volatility = elasticity_result.mape * 0.7 if elasticity_result.model_trained else 0.15
        mc = self.mc_simulator.simulate(base_value=net_promo_margin, volatility=volatility)
        confidence = elasticity_result.confidence * 0.7 + min(params.promotion_days / 30, 1.0) * 0.3

        risks = []
        if params.cannibalization_rate > 0.25:
            risks.append({"name": "Высокая каннибализация", "probability": 0.7, "impact": "high", "description": f"{params.cannibalization_rate:.0%} продаж будут 'забраны' из соседних периодов"})
        if margin_delta < 0:
            risks.append({"name": "Потеря маржи", "probability": 0.9, "impact": "high", "description": f"Маржа упадёт на {abs(margin_delta):,.0f} ₽"})

        recs: list[str] = []
        if margin_delta > 0 and long_term_benefit > 0:
            recs.append(f"Акция выгодна: {margin_delta:+,.0f} ₽ маржи + {long_term_benefit:,.0f} ₽ от новых клиентов")
        elif margin_delta < 0:
            recs.append(f"Акция убыточна: {margin_delta:+,.0f} ₽")
        if params.discount_percent > 25:
            recs.append("Ограничьте срок акции (не более 2 недель)")
        if confidence < 0.6:
            recs.append("Проведите пилот на малой группе перед массовым запуском")
        if volume_boost_pct < params.discount_percent * 0.5:
            recs.append("Спрос слабо реагирует на скидку — рассмотрите другие методы продвижения")

        return ScenarioResult(
            scenario_type=self.scenario_type,
            scenario_name=f"Скидка {params.discount_percent}% на {params.promotion_days} дней",
            entity_name=params.entity_name,
            baseline_metrics={"revenue": total_baseline_rev, "margin": total_baseline_margin, "daily_volume": baseline_daily_vol},
            projected_metrics={"revenue": net_promo_rev, "margin": net_promo_margin, "daily_volume": promo_daily_vol, "cannibalization": cannibalization_loss, "long_term": long_term_benefit},
            delta_metrics={"revenue": revenue_delta, "margin": margin_delta},
            delta_percent={"revenue": revenue_delta_pct, "margin": margin_delta_pct, "volume": volume_boost_pct},
            confidence=confidence,
            confidence_interval=mc.confidence_interval,
            risks=risks,
            recommendations=recs,
            additional_data={"elasticity": elasticity_pred.elasticity, "promo_price": promo_price, "baseline_price": baseline_price},
            formatted_summary=f"🎯 Скидка {params.discount_percent}% | Выручка: {total_baseline_rev:,.0f}→{net_promo_rev:,.0f} ({revenue_delta_pct:+.1f}%) | Маржа: {total_baseline_margin:,.0f}→{net_promo_margin:,.0f} ({margin_delta_pct:+.1f}%) | Уверенность: {confidence:.0%}",
        )
