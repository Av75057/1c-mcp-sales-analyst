#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os

os.environ["USE_MOCK_DATA"] = "true"

from src.whatif.engine.simulator import WhatIfSimulator
from src.whatif.models import SimulationRequest


async def main() -> None:
    print("=" * 60)
    print("🔮 What-If Simulator — Демо")
    print("=" * 60)

    scenarios = [
        SimulationRequest(
            scenario_type="price_change",
            entity_type="nomenclature",
            entity_name="Гвоздь 100мм",
            parameters={"change_percent": 10, "period_days": 30},
        ),
        SimulationRequest(
            scenario_type="price_change",
            entity_type="nomenclature",
            entity_name="Дрель ударная",
            parameters={"change_percent": -15, "period_days": 30},
        ),
    ]

    simulator = WhatIfSimulator()

    for req in scenarios:
        print(f"\n{'=' * 60}")
        print(f"📊 СЦЕНАРИЙ: {req.scenario_type}")
        print(f"   {req.entity_name}: изменение цены на {req.parameters['change_percent']}%")
        print(f"{'=' * 60}")

        result = await simulator.simulate(req)

        if not result.baseline.volume:
            print("❌ Недостаточно данных")
            continue

        print(f"\n💰 БАЗОВЫЕ МЕТРИКИ (за {req.parameters['period_days']} дней):")
        print(f"   Выручка: {result.baseline.revenue:,.0f} ₽")
        print(f"   Объём:   {result.baseline.volume:.0f} шт")
        print(f"   Средняя цена: {result.baseline.avg_price:.2f} ₽")

        print(f"\n📈 ПРОГНОЗ:")
        print(f"   Выручка: {result.projected.revenue:,.0f} ₽ ({result.delta.revenue:+,.0f} ₽)")
        print(f"   Объём:   {result.projected.volume:.0f} шт ({result.delta.volume:+,.0f} шт)")
        print(f"   Средняя цена: {result.projected.avg_price:.2f} ₽")

        print(f"\n📊 ЭЛАСТИЧНОСТЬ СПРОСА:")
        if result.baseline.volume:
            elasticity = result.delta.volume / result.baseline.volume * 100 / req.parameters["change_percent"]
            print(f"   Коэффициент: {elasticity:.3f}")
        else:
            print("   Н/Д")

        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        for r in result.recommendations:
            print(f"   • {r}")

        print(f"\n⚠️ РИСКИ:")
        for r in result.risks:
            print(f"   • {r.name} (вероятность: {r.probability:.0%})")

        print(f"\n🎯 УВЕРЕННОСТЬ ПРОГНОЗА: {result.confidence:.0%}")
        print(f"   Confidence interval (80%): [{result.confidence_interval['revenue_low']:,.0f} — {result.confidence_interval['revenue_high']:,.0f}]")

    print(f"\n{'=' * 60}")
    print("✅ Демо завершено")


if __name__ == "__main__":
    asyncio.run(main())
