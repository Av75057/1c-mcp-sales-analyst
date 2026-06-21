from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.logger import logger
from src.whatif.models.monte_carlo import MonteCarloSimulator
from src.whatif.scenarios.base import BaseScenario, ScenarioResult


@dataclass
class EmployeeDepartureParams:
    employee_name: str = ""
    employee_role: str = "sales_manager"
    clients_data: pd.DataFrame = field(default_factory=pd.DataFrame)
    monthly_revenue: float = 0.0
    years_in_company: int = 3
    deals_count: int = 0
    avg_deal_size: float = 0.0
    handover_period_days: int = 14
    has_replacement: bool = True
    replacement_readiness: float = 0.7


class EmployeeDepartureScenario(BaseScenario):
    def __init__(self) -> None:
        super().__init__()
        self.scenario_type = "employee_departure"
        self.scenario_name = "Увольнение сотрудника"
        self.mc_simulator = MonteCarloSimulator(iterations=1000)

    def simulate(self, params: EmployeeDepartureParams) -> ScenarioResult:
        logger.info("EmployeeDeparture: {} | стаж {} лет", params.employee_name, params.years_in_company)

        df = params.clients_data.copy()
        df["churn_prob"] = 0.2
        if "relationship_years" in df.columns:
            df["churn_prob"] += (df["relationship_years"] / 10) * 0.4
            df["churn_prob"] = df["churn_prob"].clip(upper=0.95)
        if "is_key_account" in df.columns:
            df.loc[df["is_key_account"], "churn_prob"] += 0.15
        if "last_order_days_ago" in df.columns:
            df.loc[df["last_order_days_ago"] < 30, "churn_prob"] -= 0.1
            df.loc[df["last_order_days_ago"] > 90, "churn_prob"] = 0.9
        df["churn_prob"] = df["churn_prob"].clip(0.05, 0.95)
        df["expected_loss"] = df["monthly_revenue"] * df["churn_prob"]

        total_expected_monthly = float(df["expected_loss"].sum())
        mitigation = 0.3
        if params.has_replacement:
            mitigation += 0.3 * params.replacement_readiness
        if params.handover_period_days >= 30:
            mitigation += 0.2
        elif params.handover_period_days >= 14:
            mitigation += 0.1
        mitigation = min(mitigation, 0.85)

        base_loss = total_expected_monthly * (1 - mitigation)
        pessimistic = base_loss * 1.5 * 3
        realistic = base_loss * 3
        optimistic = base_loss * 0.6 * 3

        volatility = (pessimistic - optimistic) / (4 * realistic) if realistic > 0 else 0.3
        volatility = min(max(volatility, 0.1), 0.5)
        mc = self.mc_simulator.simulate(base_value=realistic, volatility=volatility)

        at_risk = df[df["churn_prob"] > 0.7]
        high_value = at_risk[at_risk["monthly_revenue"] > params.monthly_revenue * 0.05] if params.monthly_revenue > 0 else at_risk

        confidence = 0.6 + (0.1 if params.has_replacement else 0) + min(params.years_in_company / 10, 0.2)
        confidence = min(confidence, 0.85)

        risks = []
        if len(high_value) > 0:
            risks.append({"name": "Потеря ключевых клиентов", "probability": 0.7, "impact": "high", "description": f"{len(high_value)} клиентов с высокой вероятностью ухода"})
        if not params.has_replacement:
            risks.append({"name": "Нет готовой замены", "probability": 0.9, "impact": "high", "description": "Период поиска — 2-3 месяца потерь"})

        recs: list[str] = []
        recs.append(f"Прогноз потерь за 3 мес: {realistic:,.0f} ₽ ({realistic / (params.monthly_revenue * 3) * 100:.0f}%)")
        if len(high_value) > 0:
            top = high_value.nlargest(3, "monthly_revenue")
            recs.append(f"Клиенты в зоне риска: {', '.join(top['client_name'].tolist())}")
        recs.append("Провести совместные встречи менеджера и замены с топ-10 клиентами")
        recs.append("Отправить клиентам письма о новом менеджере")
        if params.handover_period_days < 30:
            recs.append(f"Увеличить период передачи с {params.handover_period_days} до 30+ дней")

        return ScenarioResult(
            scenario_type=self.scenario_type,
            scenario_name=f"Увольнение {params.employee_name}",
            entity_name=params.employee_name,
            baseline_metrics={"monthly_revenue": params.monthly_revenue, "clients": len(df), "key_accounts": int(df["is_key_account"].sum()) if "is_key_account" in df.columns else 0, "avg_relationship_years": float(df["relationship_years"].mean()) if "relationship_years" in df.columns else 0},
            projected_metrics={"pessimistic_loss_3m": pessimistic, "realistic_loss_3m": realistic, "optimistic_loss_3m": optimistic, "at_risk_clients": len(at_risk), "high_value_at_risk": len(high_value)},
            delta_metrics={"revenue_impact": realistic / (params.monthly_revenue * 3) * 100 if params.monthly_revenue > 0 else 0},
            delta_percent={"revenue_impact": -(realistic / (params.monthly_revenue * 3) * 100) if params.monthly_revenue > 0 else 0},
            confidence=confidence,
            confidence_interval=mc.confidence_interval,
            risks=risks,
            recommendations=recs,
            additional_data={},
            formatted_summary=f"👤 {params.employee_name} ({params.employee_role}) | Стаж: {params.years_in_company} лет | Потери: {realistic:,.0f} ₽ за 3 мес ({realistic / (params.monthly_revenue * 3) * 100:.0f}%) | Уверенность: {confidence:.0%}",
        )
