#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from src.whatif.engine.financial_calculator import FinancialCalculator
from src.whatif.models.elasticity_model import ElasticityModel
from src.whatif.models.monte_carlo import MonteCarloSimulator
from src.whatif.scenarios.price_change import PriceChangeScenario


def demo_elasticity() -> None:
    print("=" * 60)
    print("📌 ElasticityModel — эластичность спроса")
    print("=" * 60)

    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=365, freq="D")
    prices = 100 + np.linspace(0, 20, 365) + np.random.normal(0, 5, 365)
    true_e = -0.7
    quantities = 1000 * (prices / 100) ** true_e * np.random.normal(1, 0.1, 365)
    quantities = np.maximum(quantities, 0)

    df = pd.DataFrame({"date": dates, "price": prices, "quantity": quantities, "weekday": np.array([d.weekday() for d in dates])})
    print(f"  Данных: {len(df)} записей, цена {df['price'].min():.0f}–{df['price'].max():.0f}")

    model = ElasticityModel()
    result = model.fit(df)
    print(f"  Эластичность: {result.elasticity:.3f}")
    print(f"  R²: {result.r2_score:.3f}")
    print(f"  Спрос {'эластичный' if result.is_elastic else 'неэластичный'}")

    for chg in [-10, -5, 5, 10, 20]:
        pred = model.predict(chg)
        print(f"  Цена {chg:+d}% → объём {pred.volume_change_percent:+.1f}% (уверенность {pred.confidence:.0%})")


def demo_monte_carlo() -> None:
    print("\n" + "=" * 60)
    print("📌 MonteCarloSimulator — 1000 итераций")
    print("=" * 60)

    sim = MonteCarloSimulator(iterations=10000)
    r = sim.simulate(base_value=1_000_000, volatility=0.15, confidence_level=0.8)
    print(f"  Медиана: {r.median:,.0f}")
    print(f"  80% CI: [{r.confidence_interval[0]:,.0f}, {r.confidence_interval[1]:,.0f}]")
    print(f"  Вероятность роста: {r.probability_positive:.1%}")


def demo_financial() -> None:
    print("\n" + "=" * 60)
    print("📌 FinancialCalculator — финансы")
    print("=" * 60)

    r = FinancialCalculator.calculate_price_change_impact(baseline_price=100, baseline_quantity=1000, baseline_cost_per_unit=60, price_change_percent=10, volume_change_percent=-6, period_days=30)
    print(f"  Выручка: {r.baseline_revenue:,.0f} → {r.projected_revenue:,.0f} ({r.revenue_delta_percent:+.1f}%)")
    print(f"  Маржа:   {r.baseline_margin:,.0f} → {r.projected_margin:,.0f} ({r.margin_delta_percent:+.1f}%)")

    r2 = FinancialCalculator.calculate_investment_impact(baseline_revenue=1_800_000, baseline_cost=1_500_000, projected_revenue=2_250_000, projected_cost=1_850_000, investment_cost=4_200_000, period_months=12)
    print(f"  ROI: {r2.roi_percent:.1f}%, окупаемость: {r2.payback_months:.1f} мес")


def demo_scenario() -> None:
    print("\n" + "=" * 60)
    print("📌 PriceChangeScenario — полный цикл")
    print("=" * 60)

    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=365, freq="D")
    prices = 100 + np.linspace(0, 20, 365) + np.random.normal(0, 5, 365)
    quantities = np.maximum(1000 * (prices / 100) ** -0.7 * np.random.normal(1, 0.1, 365), 0)
    df = pd.DataFrame({"date": dates, "price": prices, "quantity": quantities})

    scenario = PriceChangeScenario()

    for change, label in [(10, "Повышение +10%"), (-10, "Снижение -10%")]:
        r = scenario.simulate(entity_name="Гвоздь 100мм", historical_data=df, price_change_percent=change, cost_per_unit=60, period_days=30)
        print(f"\n  {label}:")
        print(f"  Эластичность: {r.elasticity:.3f}, спрос {'эластичный' if r.is_elastic else 'неэластичный'}")
        print(f"  Выручка: {r.financial.baseline_revenue:>10,.0f} → {r.financial.projected_revenue:>10,.0f} ₽ ({r.financial.revenue_delta_percent:+.1f}%)")
        print(f"  Маржа:   {r.financial.baseline_margin:>10,.0f} → {r.financial.projected_margin:>10,.0f} ₽ ({r.financial.margin_delta_percent:+.1f}%)")
        print(f"  MC медиана: {r.mc_revenue_median:,.0f} (CI: {r.mc_revenue_ci_lower:,.0f}–{r.mc_revenue_ci_upper:,.0f})")
        print(f"  Уверенность: {r.overall_confidence:.0%}")
        for i, rec in enumerate(r.recommendations, 1):
            print(f"  {i}. {rec}")


def main() -> None:
    print("\n" + " " * 20 + "🔮 ДЕМО: WHAT-IF СИМУЛЯТОР")
    demo_elasticity()
    demo_monte_carlo()
    demo_financial()
    demo_scenario()
    print("\n" + "=" * 60)
    print("✅ Все модули работают!")
    print("=" * 60)


if __name__ == "__main__":
    main()
