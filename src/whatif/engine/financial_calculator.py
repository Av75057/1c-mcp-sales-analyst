from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FinancialResult:
    baseline_revenue: float = 0.0
    baseline_cost: float = 0.0
    baseline_margin: float = 0.0
    baseline_margin_percent: float = 0.0
    projected_revenue: float = 0.0
    projected_cost: float = 0.0
    projected_margin: float = 0.0
    projected_margin_percent: float = 0.0
    revenue_delta: float = 0.0
    revenue_delta_percent: float = 0.0
    margin_delta: float = 0.0
    margin_delta_percent: float = 0.0
    roi_percent: float | None = None
    payback_months: float | None = None
    additional_costs: float = 0.0
    additional_costs_description: str = ""


class FinancialCalculator:
    @staticmethod
    def calculate_price_change_impact(
        baseline_price: float,
        baseline_quantity: float,
        baseline_cost_per_unit: float,
        price_change_percent: float,
        volume_change_percent: float,
        period_days: int = 30,
    ) -> FinancialResult:
        baseline_revenue = baseline_price * baseline_quantity
        baseline_cost = baseline_cost_per_unit * baseline_quantity
        baseline_margin = baseline_revenue - baseline_cost
        baseline_margin_percent = (baseline_margin / baseline_revenue * 100) if baseline_revenue > 0 else 0

        projected_price = baseline_price * (1 + price_change_percent / 100)
        projected_quantity = baseline_quantity * (1 + volume_change_percent / 100)
        projected_revenue = projected_price * projected_quantity
        projected_cost = baseline_cost_per_unit * projected_quantity
        projected_margin = projected_revenue - projected_cost
        projected_margin_percent = (projected_margin / projected_revenue * 100) if projected_revenue > 0 else 0

        revenue_delta = projected_revenue - baseline_revenue
        revenue_delta_percent = (revenue_delta / baseline_revenue * 100) if baseline_revenue > 0 else 0
        margin_delta = projected_margin - baseline_margin
        margin_delta_percent = (margin_delta / baseline_margin * 100) if baseline_margin > 0 else 0

        return FinancialResult(
            baseline_revenue=baseline_revenue,
            baseline_cost=baseline_cost,
            baseline_margin=baseline_margin,
            baseline_margin_percent=baseline_margin_percent,
            projected_revenue=projected_revenue,
            projected_cost=projected_cost,
            projected_margin=projected_margin,
            projected_margin_percent=projected_margin_percent,
            revenue_delta=revenue_delta,
            revenue_delta_percent=revenue_delta_percent,
            margin_delta=margin_delta,
            margin_delta_percent=margin_delta_percent,
        )

    @staticmethod
    def calculate_investment_impact(
        baseline_revenue: float,
        baseline_cost: float,
        projected_revenue: float,
        projected_cost: float,
        investment_cost: float,
        period_months: int = 12,
    ) -> FinancialResult:
        baseline_margin = baseline_revenue - baseline_cost
        baseline_margin_percent = (baseline_margin / baseline_revenue * 100) if baseline_revenue > 0 else 0
        projected_margin = projected_revenue - projected_cost
        projected_margin_percent = (projected_margin / projected_revenue * 100) if projected_revenue > 0 else 0

        revenue_delta = projected_revenue - baseline_revenue
        revenue_delta_percent = (revenue_delta / baseline_revenue * 100) if baseline_revenue > 0 else 0
        margin_delta = projected_margin - baseline_margin
        margin_delta_percent = (margin_delta / baseline_margin * 100) if baseline_margin > 0 else 0

        additional_profit = margin_delta * period_months
        roi_percent = (additional_profit / investment_cost * 100) if investment_cost > 0 else 0
        payback_months = investment_cost / margin_delta if margin_delta > 0 else None

        return FinancialResult(
            baseline_revenue=baseline_revenue,
            baseline_cost=baseline_cost,
            baseline_margin=baseline_margin,
            baseline_margin_percent=baseline_margin_percent,
            projected_revenue=projected_revenue,
            projected_cost=projected_cost,
            projected_margin=projected_margin,
            projected_margin_percent=projected_margin_percent,
            revenue_delta=revenue_delta,
            revenue_delta_percent=revenue_delta_percent,
            margin_delta=margin_delta,
            margin_delta_percent=margin_delta_percent,
            roi_percent=roi_percent,
            payback_months=payback_months,
            additional_costs=investment_cost,
            additional_costs_description=f"Инвестиции: {investment_cost:,.0f} ₽",
        )
