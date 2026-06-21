#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json

from src.mcp.tools import ALL_TOOLS_SCHEMA, TOOLS_REGISTRY, get_tool_function
from src.whatif.mcp.tools import simulate_scenario_tool


async def demo_registry() -> None:
    print("=" * 60)
    print("📋 Реестр MCP-tools")
    print("=" * 60)
    print(f"  Всего: {len(TOOLS_REGISTRY)} tools")
    for name in TOOLS_REGISTRY:
        print(f"  • {name}")
    print(f"  Схема: {len(ALL_TOOLS_SCHEMA)} определений")


async def demo_full_cycle() -> None:
    print("\n" + "=" * 60)
    print("🎯 Полный цикл: симуляция → график")
    print("=" * 60)

    for scenario, params in [
        ("price_change", {"entity_name": "Гвоздь 100мм", "change_percent": 10}),
        ("promotion", {"entity_name": "Инструменты", "discount_percent": 15, "promotion_days": 14}),
        ("purchase_change", {"entity_name": "Саморезы", "order_size_change_percent": 50}),
        ("employee_departure", {"entity_name": "Иванов И.И.", "monthly_revenue": 2_000_000, "years_in_company": 5}),
    ]:
        print(f"\n▶ {scenario}:")
        r = await simulate_scenario_tool(scenario_type=scenario, **params)
        if r.get("success"):
            print(f"  ✅ Уверенность: {r['confidence']:.0%}")
            print(f"  {r.get('formatted_summary', '')[:100]}")
            if r.get("chart_params"):
                from src.charts.engine import render_chart
                cp = r["chart_params"]
                chart = render_chart(cp["chart_type"], cp["title"], cp["x_data"][:5], cp["y_data"][0][:5] if isinstance(cp["y_data"][0], list) else cp["y_data"][:5], cp.get("x_label", ""), cp.get("y_label", ""))
                print(f"  📊 График: {chart['chart_id']}")
        else:
            print(f"  ❌ {r.get('error')}")


async def main() -> None:
    print("🚀 WHAT-IF MCP ИНТЕГРАЦИЯ\n")
    await demo_registry()
    await demo_full_cycle()
    print("\n" + "=" * 60)
    print("✅ Интеграция завершена!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
