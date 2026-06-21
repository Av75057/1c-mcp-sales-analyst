from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.logger import logger
from src.whatif.models.monte_carlo import MonteCarloSimulator
from src.whatif.scenarios.base import BaseScenario, ScenarioResult


@dataclass
class PurchaseChangeParams:
    entity_name: str = ""
    historical_data: pd.DataFrame = field(default_factory=pd.DataFrame)
    current_order_size: float = 0.0
    current_order_frequency_days: int = 20
    purchase_price_per_unit: float = 0.0
    selling_price_per_unit: float = 0.0
    order_size_change_percent: float = 0.0
    holding_cost_percent: float = 0.02
    stockout_probability_current: float = 0.15
    avg_lost_sale_value: float = 0.0
    supplier_volume_discount: float = 0.0


class PurchaseChangeScenario(BaseScenario):
    def __init__(self) -> None:
        super().__init__()
        self.scenario_type = "purchase_change"
        self.scenario_name = "Изменение объёма закупок"
        self.mc_simulator = MonteCarloSimulator(iterations=1000)

    def simulate(self, params: PurchaseChangeParams) -> ScenarioResult:
        logger.info("PurchaseChange: {} | изменение заказа {:.0f}%", params.entity_name, params.order_size_change_percent)

        recent = params.historical_data.tail(60)
        daily_sales = float(recent["quantity"].mean())
        daily_sales_std = float(recent["quantity"].std()) if "quantity" in recent else daily_sales * 0.3

        current_days_of_stock = params.current_order_size / daily_sales if daily_sales > 0 else 0
        current_avg_stock = params.current_order_size / 2
        current_frozen_money = current_avg_stock * params.purchase_price_per_unit
        current_monthly_stockout_loss = (params.stockout_probability_current * params.avg_lost_sale_value * 30 / params.current_order_frequency_days) if params.avg_lost_sale_value > 0 else 0

        new_order_size = params.current_order_size * (1 + params.order_size_change_percent / 100)
        new_days_of_stock = new_order_size / daily_sales if daily_sales > 0 else 0
        new_avg_stock = new_order_size / 2
        new_frozen_money = new_avg_stock * params.purchase_price_per_unit
        size_ratio = params.current_order_size / new_order_size if new_order_size > 0 else 1
        new_stockout_probability = max(0.01, min(params.stockout_probability_current * (size_ratio ** 1.5), 0.99))
        new_monthly_stockout_loss = (new_stockout_probability * params.avg_lost_sale_value * 30 / params.current_order_frequency_days) if params.avg_lost_sale_value > 0 else 0

        supplier_savings = 0
        if params.supplier_volume_discount > 0 and params.order_size_change_percent > 0:
            monthly_purchase = daily_sales * 30 * params.purchase_price_per_unit
            supplier_savings = monthly_purchase * params.supplier_volume_discount / 100

        current_holding_cost = current_frozen_money * params.holding_cost_percent
        new_holding_cost = new_frozen_money * params.holding_cost_percent
        holding_cost_delta = new_holding_cost - current_holding_cost
        stockout_savings = current_monthly_stockout_loss - new_monthly_stockout_loss
        net_monthly_benefit = stockout_savings + supplier_savings - holding_cost_delta

        volatility = min((daily_sales_std / daily_sales) if daily_sales > 0 else 0.3, 0.5)
        mc = self.mc_simulator.simulate(base_value=net_monthly_benefit, volatility=volatility)
        confidence = max(0.4, 1.0 - volatility)

        optimal_eoq = self._eoq(daily_sales, params.purchase_price_per_unit, params.holding_cost_percent)

        risks = []
        if new_days_of_stock > 60:
            risks.append({"name": "Избыточные остатки", "probability": 0.7, "impact": "high", "description": f"Запас на {new_days_of_stock:.0f} дней"})
        if params.order_size_change_percent < -30:
            risks.append({"name": "Высокий риск stock-out", "probability": 0.8, "impact": "high", "description": f"Stock-out {new_stockout_probability:.0%}"})

        recs: list[str] = []
        if net_monthly_benefit > 0:
            recs.append(f"✅ Изменение выгодно: +{net_monthly_benefit:,.0f} ₽/мес")
        else:
            recs.append(f"❌ Изменение невыгодно: {net_monthly_benefit:,.0f} ₽/мес")
        if current_days_of_stock < 7 and params.order_size_change_percent > 0:
            recs.append(f"Запас ({current_days_of_stock:.0f} дней) критически мал — увеличение оправдано")
        if new_days_of_stock > 90:
            recs.append(f"Запас на {new_days_of_stock:.0f} дней избыточен")
        if optimal_eoq and abs(params.current_order_size - optimal_eoq) / optimal_eoq > 0.2:
            recs.append(f"Оптимальный EOQ: {optimal_eoq:,.0f} шт (сейчас {params.current_order_size:,.0f})")

        return ScenarioResult(
            scenario_type=self.scenario_type,
            scenario_name=f"Заказ {params.order_size_change_percent:+.0f}%",
            entity_name=params.entity_name,
            baseline_metrics={"order_size": params.current_order_size, "days_of_stock": current_days_of_stock, "frozen_money": current_frozen_money, "stockout_prob": params.stockout_probability_current, "stockout_loss": current_monthly_stockout_loss, "holding_cost": current_holding_cost},
            projected_metrics={"order_size": new_order_size, "days_of_stock": new_days_of_stock, "frozen_money": new_frozen_money, "stockout_prob": new_stockout_probability, "stockout_loss": new_monthly_stockout_loss, "holding_cost": new_holding_cost, "supplier_savings": supplier_savings, "stockout_savings": stockout_savings},
            delta_metrics={"order_size": new_order_size - params.current_order_size, "net_monthly_benefit": net_monthly_benefit, "frozen_money_delta": new_frozen_money - current_frozen_money},
            delta_percent={"order_size": params.order_size_change_percent, "stockout_prob_delta": (new_stockout_probability - params.stockout_probability_current) / params.stockout_probability_current * 100 if params.stockout_probability_current > 0 else 0},
            confidence=confidence,
            confidence_interval=mc.confidence_interval,
            risks=risks,
            recommendations=recs,
            additional_data={"optimal_eoq": optimal_eoq if optimal_eoq else 0, "daily_sales": daily_sales},
            formatted_summary=f"📦 Закупки {params.entity_name}: заказ {params.current_order_size:,.0f}→{new_order_size:,.0f} ({params.order_size_change_percent:+.0f}%) | Чистый эффект: {net_monthly_benefit:+,.0f} ₽/мес | Уверенность: {confidence:.0%}",
        )

    def _eoq(self, daily_sales: float, purchase_price: float, holding_pct: float) -> float | None:
        try:
            annual = daily_sales * 365
            order_cost = 5000
            h = purchase_price * holding_pct * 12
            if h <= 0:
                return None
            return float(np.sqrt(2 * annual * order_cost / h))
        except Exception:
            return None
