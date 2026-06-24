#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from src.whatif.engine.simulator import WhatIfSimulator
from src.whatif.scenarios.promotion import PromotionParams, PromotionScenario
from src.whatif.scenarios.purchase_change import PurchaseChangeParams, PurchaseChangeScenario
from src.whatif.scenarios.employee_departure import EmployeeDepartureParams, EmployeeDepartureScenario


def demo_promotion() -> None:
    print("=" * 60)
    print("📌 СЦЕНАРИЙ 1: Promotion (Акция/Скидка)")
    print("=" * 60)
    np.random.seed(42)
    df = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=365, freq="D"), "price": 1000 + np.random.normal(0, 20, 365), "quantity": np.maximum(50 * (1000 / (1000 + np.random.normal(0, 20, 365))) ** -1.3 * np.random.normal(1, 0.15, 365), 0)})

    scenario = PromotionScenario()
    for disc, days in [(15, 14), (30, 7)]:
        r = scenario.simulate(PromotionParams(entity_name="Инструменты", historical_data=df, discount_percent=disc, promotion_days=days, cost_per_unit=600))
        print(f"\n  Скидка {disc}% на {days} дней:")
        print(f"    Выручка: {r.baseline_metrics['revenue']:,.0f} → {r.projected_metrics['revenue']:,.0f}")
        print(f"    Маржа:   {r.baseline_metrics['margin']:,.0f} → {r.projected_metrics['margin']:,.0f} ({r.delta_percent['margin']:+.1f}%)")
        print(f"    Долгосрочный эффект: +{r.projected_metrics.get('long_term', 0):,.0f}")
        print(f"    Уверенность: {r.confidence:.0%}")
        for rec in r.recommendations:
            print(f"    • {rec}")


def demo_purchase() -> None:
    print("\n" + "=" * 60)
    print("📌 СЦЕНАРИЙ 2: PurchaseChange (Закупки)")
    print("=" * 60)
    np.random.seed(42)
    df = pd.DataFrame({"date": pd.date_range("2025-12-01", periods=180, freq="D"), "quantity": np.maximum(np.random.normal(100, 25, 180), 10)})

    scenario = PurchaseChangeScenario()
    params = PurchaseChangeParams(entity_name="Гвоздь 100мм", historical_data=df, current_order_size=2000, current_order_frequency_days=20, purchase_price_per_unit=8, selling_price_per_unit=15, order_size_change_percent=50, avg_lost_sale_value=150_000)
    r = scenario.simulate(params)
    print(f"\n  Увеличение заказа на 50%:")
    print(f"    Заказ: {r.baseline_metrics['order_size']:,.0f} → {r.projected_metrics['order_size']:,.0f} шт")
    print(f"    Stock-out: {r.baseline_metrics['stockout_prob']:.0%} → {r.projected_metrics['stockout_prob']:.0%}")
    print(f"    Чистый эффект: {r.delta_metrics['net_monthly_benefit']:+,.0f} ₽/мес")
    for rec in r.recommendations:
        print(f"    • {rec}")


def demo_employee() -> None:
    print("\n" + "=" * 60)
    print("📌 СЦЕНАРИЙ 3: EmployeeDeparture (Увольнение)")
    print("=" * 60)
    np.random.seed(42)
    n = 85
    clients = pd.DataFrame({
        "client_name": [f"Клиент {i}" for i in range(1, n + 1)],
        "monthly_revenue": np.concatenate([np.random.normal(150_000, 50_000, 10), np.random.normal(50_000, 20_000, 25), np.random.normal(15_000, 5_000, 50)]).clip(min=1000),
        "relationship_years": np.concatenate([np.random.uniform(3, 7, 10), np.random.uniform(1, 4, 25), np.random.uniform(0.3, 2, 50)]),
        "last_order_days_ago": np.random.exponential(20, n).clip(min=1),
        "is_key_account": [True] * 10 + [False] * (n - 10),
    })

    scenario = EmployeeDepartureScenario()
    params = EmployeeDepartureParams(employee_name="Иванов И.И.", employee_role="sales_manager", clients_data=clients, monthly_revenue=float(clients["monthly_revenue"].sum()), years_in_company=5, deals_count=342, avg_deal_size=68_000)
    r = scenario.simulate(params)
    print(f"\n  {params.employee_name} ({params.employee_role}):")
    print(f"    Выручка/мес: {r.baseline_metrics['monthly_revenue']:,.0f}")
    print(f"    Клиентов: {r.baseline_metrics['clients']}")
    print(f"    Потери (реалистичный): {r.projected_metrics['realistic_loss_3m']:,.0f} за 3 мес")
    print(f"    Уверенность: {r.confidence:.0%}")
    for rec in r.recommendations[:3]:
        print(f"    • {rec}")


def demo_simulator() -> None:
    print("\n" + "=" * 60)
    print("📌 WhatIfSimulator — роутер")
    print("=" * 60)
    sim = WhatIfSimulator()
    for s in sim.list_scenarios():
        print(f"  • {s['type']}: {s['name']} — {s['description']}")


def main() -> None:
    print(" " * 15 + "🔮 WHAT-IF v2: ВСЕ СЦЕНАРИИ")
    demo_promotion()
    demo_purchase()
    demo_employee()
    demo_simulator()
    print("\n" + "=" * 60)
    print("✅ Все 4 сценария работают!")
    print("=" * 60)


if __name__ == "__main__":
    main()
