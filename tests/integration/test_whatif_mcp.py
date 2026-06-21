from __future__ import annotations

import pytest

from src.mcp.tools import ALL_TOOLS_SCHEMA, TOOLS_REGISTRY, get_tool_function
from src.whatif.mcp.tools import list_whatif_scenarios_tool


def test_all_tools_registered():
    assert "simulate_scenario" in TOOLS_REGISTRY
    assert "list_whatif_scenarios" in TOOLS_REGISTRY
    assert len(TOOLS_REGISTRY) >= 7


def test_all_tools_schema():
    names = [t["function"]["name"] for t in ALL_TOOLS_SCHEMA]
    assert "simulate_scenario" in names
    assert len(ALL_TOOLS_SCHEMA) >= 7


def test_get_tool_function():
    func = get_tool_function("simulate_scenario")
    assert callable(func)
    with pytest.raises(ValueError):
        get_tool_function("nonexistent")


def test_list_scenarios():
    r = list_whatif_scenarios_tool()
    assert r["total"] == 4


@pytest.mark.asyncio
async def test_simulate_price_change():
    from src.whatif.mcp.tools import simulate_scenario_tool as sim
    r = await sim(scenario_type="price_change", entity_name="Test", change_percent=10)
    assert r["success"] is True
    assert r["confidence"] > 0
    assert r.get("chart_params") is not None


@pytest.mark.asyncio
async def test_simulate_promotion():
    from src.whatif.mcp.tools import simulate_scenario_tool as sim
    r = await sim(scenario_type="promotion", entity_name="Test", discount_percent=15, promotion_days=14)
    assert r["success"] is True


@pytest.mark.asyncio
async def test_simulate_purchase():
    from src.whatif.mcp.tools import simulate_scenario_tool as sim
    r = await sim(scenario_type="purchase_change", entity_name="Test", order_size_change_percent=50)
    assert r["success"] is True


@pytest.mark.asyncio
async def test_simulate_employee():
    from src.whatif.mcp.tools import simulate_scenario_tool as sim
    r = await sim(scenario_type="employee_departure", entity_name="Test", monthly_revenue=1_000_000)
    assert r["success"] is True
    assert "realistic_loss_3m" in r["projected_metrics"]


@pytest.mark.asyncio
async def test_simulate_missing_params():
    from src.whatif.mcp.tools import simulate_scenario_tool as sim
    r = await sim(scenario_type="employee_departure", entity_name="Test")
    assert r["success"] is True
    assert "risks" in r


@pytest.mark.asyncio
async def test_risks_and_recommendations():
    from src.whatif.mcp.tools import simulate_scenario_tool as sim
    r = await sim(scenario_type="employee_departure", entity_name="Test", monthly_revenue=1_000_000)
    assert len(r["recommendations"]) > 0


@pytest.mark.asyncio
async def test_formatted_summary():
    from src.whatif.mcp.tools import simulate_scenario_tool as sim
    r = await sim(scenario_type="promotion", entity_name="Test", discount_percent=15, promotion_days=14)
    assert len(r.get("formatted_summary", "")) > 0
