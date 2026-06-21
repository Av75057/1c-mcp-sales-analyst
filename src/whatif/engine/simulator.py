from __future__ import annotations

from typing import Any, Literal

from src.logger import logger
from src.whatif.scenarios.base import ScenarioResult
from src.whatif.scenarios.employee_departure import EmployeeDepartureParams, EmployeeDepartureScenario
from src.whatif.scenarios.price_change import PriceChangeScenario
from src.whatif.scenarios.promotion import PromotionParams, PromotionScenario
from src.whatif.scenarios.purchase_change import PurchaseChangeParams, PurchaseChangeScenario

ScenarioType = Literal["price_change", "promotion", "purchase_change", "employee_departure"]


class WhatIfSimulator:
    def __init__(self) -> None:
        self._scenarios: dict[str, Any] = {
            "price_change": PriceChangeScenario(),
            "promotion": PromotionScenario(),
            "purchase_change": PurchaseChangeScenario(),
            "employee_departure": EmployeeDepartureScenario(),
        }

    def list_scenarios(self) -> list[dict[str, str]]:
        return [
            {"type": "price_change", "name": "Изменение цены", "description": "Прогноз эффекта от изменения цены", "example": "Что будет, если поднять цены на 10%?"},
            {"type": "promotion", "name": "Акция/Скидка", "description": "Прогноз эффекта от временной скидки", "example": "Что будет, если сделать скидку 15% на 2 недели?"},
            {"type": "purchase_change", "name": "Изменение закупок", "description": "Оптимизация размера заказа", "example": "Что будет, если закупать на 50% больше?"},
            {"type": "employee_departure", "name": "Увольнение сотрудника", "description": "Прогноз потерь от увольнения", "example": "Что будет, если менеджер уволится?"},
        ]

    async def simulate(self, scenario_type: ScenarioType, **kwargs: Any) -> ScenarioResult:
        if scenario_type not in self._scenarios:
            raise ValueError(f"Неизвестный сценарий: {scenario_type}")
        logger.info("Simulator: {} → {}", scenario_type, kwargs.get("entity_name", ""))
        scenario = self._scenarios[scenario_type]

        if scenario_type == "promotion":
            params = PromotionParams(**kwargs)
        elif scenario_type == "purchase_change":
            params = PurchaseChangeParams(**kwargs)
        elif scenario_type == "employee_departure":
            params = EmployeeDepartureParams(**kwargs)
        else:
            r = scenario.simulate(**kwargs)
            return ScenarioResult(
                scenario_type=scenario_type,
                scenario_name=r.scenario_name if hasattr(r, "scenario_name") else r.entity_name,
                entity_name=r.entity_name if hasattr(r, "entity_name") else "",
                baseline_metrics={"revenue": r.financial.baseline_revenue if hasattr(r, "financial") else 0},
                projected_metrics={"revenue": r.financial.projected_revenue if hasattr(r, "financial") else 0},
                delta_percent={"revenue": r.financial.revenue_delta_percent if hasattr(r, "financial") else 0, "margin": r.financial.margin_delta_percent if hasattr(r, "financial") else 0},
                confidence=r.overall_confidence if hasattr(r, "overall_confidence") else 0.5,
                risks=[{"name": risk.name, "probability": risk.probability, "impact": risk.impact} for risk in r.risks] if hasattr(r, "risks") else [],
                recommendations=r.recommendations if hasattr(r, "recommendations") else [],
            )

        return scenario.simulate(params)
