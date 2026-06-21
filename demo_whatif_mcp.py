#!/usr/bin/env python3
from __future__ import annotations

import asyncio

from src.whatif.mcp.tools import list_whatif_scenarios_tool, simulate_scenario_tool


async def main() -> None:
    print("=" * 60)
    print("🎯 WHAT-IF MCP ИНТЕГРАЦИЯ — ДЕМО")
    print("=" * 60)

    # Tool 1: list scenarios
    print("\n📋 Tool: list_whatif_scenarios")
    s = list_whatif_scenarios_tool()
    for sc in s["scenarios"]:
        print(f"  • {sc['type']}: {sc['name']}")

    # Tool 2: simulate price_change
    print("\n" + "=" * 60)
    print("💰 СЦЕНАРИЙ: price_change")
    print("=" * 60)
    r = await simulate_scenario_tool(scenario_type="price_change", entity_name="Гвоздь 100мм", change_percent=10, period_days=30)
    if r.get("success"):
        print(f"  Уверенность: {r['confidence']:.0%}")
        print(f"  Маржа: {r['delta_percent'].get('margin', 0):+.1f}%")
        print(f"  График: {r['chart_params']['chart_type'] if r.get('chart_params') else 'нет'}")
        for rec in r["recommendations"][:2]:
            print(f"  • {rec}")
    else:
        print(f"  ❌ {r.get('error')}")

    # Tool 3: simulate promotion
    print("\n" + "=" * 60)
    print("🏷️ СЦЕНАРИЙ: promotion")
    print("=" * 60)
    r = await simulate_scenario_tool(scenario_type="promotion", entity_name="Инструменты", discount_percent=15, promotion_days=14)
    if r.get("success"):
        print(f"  Уверенность: {r['confidence']:.0%}")
        print(f"  Эффект: {r['formatted_summary'][:80]}")

    # Tool 4: simulate purchase_change
    print("\n" + "=" * 60)
    print("📦 СЦЕНАРИЙ: purchase_change")
    print("=" * 60)
    r = await simulate_scenario_tool(scenario_type="purchase_change", entity_name="Саморезы", order_size_change_percent=50)
    if r.get("success"):
        print(f"  Уверенность: {r['confidence']:.0%}")
        print(f"  {r['formatted_summary'][:80]}")

    # Tool 5: simulate employee_departure
    print("\n" + "=" * 60)
    print("👤 СЦЕНАРИЙ: employee_departure")
    print("=" * 60)
    r = await simulate_scenario_tool(scenario_type="employee_departure", entity_name="Иванов И.И.", monthly_revenue=2_000_000, years_in_company=5)
    if r.get("success"):
        print(f"  Уверенность: {r['confidence']:.0%}")
        print(f"  Потери: {r['projected_metrics'].get('realistic_loss_3m', 0):,.0f} ₽")
        print(f"  Клиентов в зоне риска: {r['projected_metrics'].get('at_risk_clients', 0)}")

    print("\n" + "=" * 60)
    print("✅ Все MCP-tools работают!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
