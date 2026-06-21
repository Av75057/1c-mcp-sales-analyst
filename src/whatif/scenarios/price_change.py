from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.logger import logger
from src.whatif.engine.financial_calculator import FinancialCalculator, FinancialResult
from src.whatif.models.elasticity_model import ElasticityModel
from src.whatif.models.monte_carlo import MonteCarloSimulator


@dataclass
class PriceChangeResult:
    entity_name: str = ""
    baseline_price: float = 0.0
    price_change_percent: float = 0.0
    period_days: int = 30
    elasticity: float = 0.0
    elasticity_confidence: float = 0.0
    is_elastic: bool = False
    volume_change_percent: float = 0.0
    projected_price: float = 0.0
    projected_quantity: float = 0.0
    financial: FinancialResult = field(default_factory=FinancialResult)
    mc_revenue_median: float = 0.0
    mc_revenue_ci_lower: float = 0.0
    mc_revenue_ci_upper: float = 0.0
    mc_probability_positive: float = 0.0
    overall_confidence: float = 0.0
    recommendations: list[str] = field(default_factory=list)


class PriceChangeScenario:
    def __init__(self) -> None:
        self.elasticity_model = ElasticityModel()
        self.mc_simulator = MonteCarloSimulator(iterations=1000)
        self.financial_calc = FinancialCalculator()

    def simulate(
        self,
        entity_name: str,
        historical_data: pd.DataFrame,
        price_change_percent: float,
        cost_per_unit: float,
        period_days: int = 30,
    ) -> PriceChangeResult:
        logger.info("PriceChange: {} | {}% | {} дней", entity_name, price_change_percent, period_days)

        elasticity_result = self.elasticity_model.fit(historical_data)
        elasticity_pred = self.elasticity_model.predict(price_change_percent)

        recent = historical_data.tail(30)
        baseline_price = float(recent["price"].mean())
        baseline_quantity = float(recent["quantity"].mean()) * (period_days / 30)

        financial = self.financial_calc.calculate_price_change_impact(
            baseline_price=baseline_price,
            baseline_quantity=baseline_quantity,
            baseline_cost_per_unit=cost_per_unit,
            price_change_percent=price_change_percent,
            volume_change_percent=elasticity_pred.volume_change_percent,
            period_days=period_days,
        )

        volatility = elasticity_result.mape * 0.5 if elasticity_result.model_trained else 0.15
        mc_result = self.mc_simulator.simulate(base_value=financial.projected_revenue, volatility=volatility)

        projected_price = baseline_price * (1 + price_change_percent / 100)
        projected_quantity = baseline_quantity * (1 + elasticity_pred.volume_change_percent / 100)

        overall_confidence = elasticity_result.confidence * 0.5 + (1 - volatility) * 0.3 + min(len(historical_data) / 365, 1.0) * 0.2

        recommendations = self._recommendations(elasticity_pred.elasticity, elasticity_pred.is_elastic, price_change_percent, financial.margin_delta_percent, overall_confidence)

        return PriceChangeResult(
            entity_name=entity_name,
            baseline_price=baseline_price,
            price_change_percent=price_change_percent,
            period_days=period_days,
            elasticity=elasticity_pred.elasticity,
            elasticity_confidence=elasticity_result.confidence,
            is_elastic=elasticity_pred.is_elastic,
            volume_change_percent=elasticity_pred.volume_change_percent,
            projected_price=projected_price,
            projected_quantity=projected_quantity,
            financial=financial,
            mc_revenue_median=mc_result.median,
            mc_revenue_ci_lower=mc_result.confidence_interval[0],
            mc_revenue_ci_upper=mc_result.confidence_interval[1],
            mc_probability_positive=mc_result.probability_positive,
            overall_confidence=overall_confidence,
            recommendations=recommendations,
        )

    def _recommendations(self, elasticity: float, is_elastic: bool, price_change: float, margin_delta_pct: float, confidence: float) -> list[str]:
        recs: list[str] = []
        if is_elastic and price_change > 0:
            recs.append("Спрос эластичный: повышение цены сильно снизит объём. Рассмотрите меньший шаг.")
        elif not is_elastic and price_change > 0:
            recs.append("Спрос неэластичный — повышение цены выгодно. Маржа вырастет.")
        if price_change < 0 and is_elastic:
            recs.append("Снижение цены при эластичном спросе увеличит объём продаж.")
        if margin_delta_pct > 5:
            recs.append(f"Маржа вырастет на {margin_delta_pct:.1f}% — решение выгодно.")
        elif margin_delta_pct < -5:
            recs.append(f"Маржа упадёт на {abs(margin_delta_pct):.1f}% — решение невыгодно.")
        if confidence < 0.6:
            recs.append("Низкая уверенность. Протестируйте на малой группе товаров.")
        if price_change > 10:
            recs.append("Повышайте цену постепенно (по 5% за 2 недели) для минимизации оттока.")
        if confidence > 0.8:
            recs.append("Высокая уверенность — можно применять решение.")
        return recs
