from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.config import settings
from src.logger import logger
from src.whatif.engine.simulator import WhatIfSimulator
from src.whatif.mcp.chart_builder import WhatIfChartBuilder

_simulator = WhatIfSimulator()
_chart_builder = WhatIfChartBuilder()


def list_whatif_scenarios_tool() -> dict[str, Any]:
    logger.info("Tool: list_whatif_scenarios")
    return {"scenarios": _simulator.list_scenarios(), "total": 4}


async def simulate_scenario_tool(
    scenario_type: str,
    entity_name: str = "",
    change_percent: float | None = None,
    discount_percent: float | None = None,
    period_days: int = 30,
    promotion_days: int | None = None,
    order_size_change_percent: float | None = None,
    employee_name: str | None = None,
    cost_per_unit: float | None = None,
    monthly_revenue: float | None = None,
    years_in_company: int | None = None,
    deals_count: int | None = None,
    avg_deal_size: float | None = None,
    handover_period_days: int = 14,
    has_replacement: bool = True,
    replacement_readiness: float = 0.7,
) -> dict[str, Any]:
    logger.info("Tool: simulate_scenario (type={}, entity={})", scenario_type, entity_name)
    try:
        params: dict[str, Any] = {}

        if scenario_type == "price_change":
            if change_percent is None:
                return {"error": "Не указан change_percent"}
            df, is_real = _gen_test_data(price=100, qty=100, elasticity=-0.7, entity_name=entity_name)
            params = {"entity_name": entity_name or "Товар", "historical_data": df, "price_change_percent": change_percent, "cost_per_unit": cost_per_unit or 60, "period_days": period_days}

        elif scenario_type == "promotion":
            if discount_percent is None:
                return {"error": "Не указан discount_percent"}
            df, is_real = _gen_test_data(price=1000, qty=50, elasticity=-1.3, entity_name=entity_name)
            params = {"entity_name": entity_name or "Категория", "historical_data": df, "discount_percent": discount_percent, "promotion_days": promotion_days or period_days, "cost_per_unit": cost_per_unit or 600}

        elif scenario_type == "purchase_change":
            if order_size_change_percent is None:
                return {"error": "Не указан order_size_change_percent"}
            df, is_real = _gen_test_data(price=100, qty=100, elasticity=0, entity_name=entity_name)
            params = {"entity_name": entity_name or "Товар", "historical_data": df, "current_order_size": 2000, "current_order_frequency_days": 20, "purchase_price_per_unit": 8, "selling_price_per_unit": 15, "order_size_change_percent": order_size_change_percent, "avg_lost_sale_value": 150_000}

        elif scenario_type == "employee_departure":
            clients = _gen_clients()
            params = {"employee_name": employee_name or entity_name or "Сотрудник", "employee_role": "sales_manager", "clients_data": clients, "monthly_revenue": monthly_revenue or float(clients["monthly_revenue"].sum()), "years_in_company": years_in_company or 5, "deals_count": deals_count or 300, "avg_deal_size": avg_deal_size or 60_000, "handover_period_days": handover_period_days, "has_replacement": has_replacement, "replacement_readiness": replacement_readiness}

        else:
            return {"error": f"Неизвестный сценарий: {scenario_type}"}

        result = await _simulator.simulate(scenario_type, **params)
        try:
            chart = _chart_builder.build_chart_params(result)
        except Exception:
            chart = None

        return {"success": True, "use_real_data": is_real if "is_real" in dir() else False, "scenario_type": result.scenario_type, "scenario_name": result.scenario_name, "entity_name": result.entity_name, "confidence": result.confidence, "confidence_interval": list(result.confidence_interval) if result.confidence_interval else None, "baseline_metrics": result.baseline_metrics, "projected_metrics": result.projected_metrics, "delta_percent": result.delta_percent, "risks": result.risks, "recommendations": result.recommendations, "formatted_summary": result.formatted_summary, "chart_params": chart}

    except Exception as e:
        logger.error("simulate_scenario error: {}", e)
        return {"success": False, "error": str(e)}


async def _fetch_real_data(entity_name: str, days: int = 365) -> pd.DataFrame | None:
    try:
        from src.clients.c1_client import C1Client
        from datetime import date, timedelta
        c1 = C1Client()
        end = date.today()
        start = end - timedelta(days=days)
        sales = await c1.get_sales(date_from=start.isoformat(), date_to=end.isoformat())
        if not sales:
            return None
        filtered = [s for s in sales if entity_name.lower() in s.get("nomenclature", "").lower()]
        if not filtered:
            logger.warning("Нет данных о продажах для '{}' в 1С", entity_name)
            return None
        rows: list[dict] = []
            d = s.get("date", "")
            qty = s.get("quantity", 0)
            price = s.get("sum", 0) / qty if qty > 0 else 0
            if qty > 0 and price > 0:
                rows.append({"date": d, "price": price, "quantity": qty})
        if len(rows) < 10:
            return None
        return pd.DataFrame(rows)
    except Exception:
        return None


def _gen_test_data(price: float = 100, qty: float = 100, elasticity: float = -0.7, entity_name: str = "") -> tuple[pd.DataFrame, bool]:
    if not settings.use_mock_data and entity_name:
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            real = loop.run_until_complete(_fetch_real_data(entity_name))
            loop.close()
            if real is not None:
                logger.info("Используются реальные данные из 1С для '{}' ({} записей)", entity_name, len(real))
                return real, True
        except Exception:
            pass
    np.random.seed(42)
    dates = pd.date_range("2025-06-22", periods=365, freq="D")
    prices = price + np.random.normal(0, price * 0.05, 365)
    quantities = np.maximum(qty * (prices / price) ** elasticity * np.random.normal(1, 0.1, 365), 0)
    logger.warning("Симуляция на сгенерированных данных (нет истории по '{}')", entity_name)
    return pd.DataFrame({"date": dates, "price": prices, "quantity": quantities}), False


def _gen_clients() -> pd.DataFrame:
    np.random.seed(42)
    data = []
    for i in range(85):
        if i < 10:
            rev, yrs, key = np.random.normal(150_000, 50_000), np.random.uniform(3, 7), True
        elif i < 35:
            rev, yrs, key = np.random.normal(50_000, 20_000), np.random.uniform(1, 4), False
        else:
            rev, yrs, key = np.random.normal(15_000, 5_000), np.random.uniform(0.3, 2), False
        data.append({"client_name": f"Клиент {i+1}", "monthly_revenue": max(rev, 1000), "relationship_years": yrs, "last_order_days_ago": np.random.exponential(20), "is_key_account": key})
    return pd.DataFrame(data)


WHATIF_TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "list_whatif_scenarios", "description": "Список доступных сценариев 'Что если'", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "simulate_scenario", "description": "Запустить симуляцию бизнес-сценария", "parameters": {"type": "object", "properties": {"scenario_type": {"type": "string", "enum": ["price_change", "promotion", "purchase_change", "employee_departure"], "description": "Тип сценария"}, "entity_name": {"type": "string", "description": "Название товара/категории/менеджера"}, "change_percent": {"type": "number", "description": "Изменение цены в %"}, "discount_percent": {"type": "number", "description": "Скидка в %"}, "period_days": {"type": "integer", "description": "Период в днях"}, "promotion_days": {"type": "integer", "description": "Длительность акции"}, "order_size_change_percent": {"type": "number", "description": "Изменение заказа в %"}, "employee_name": {"type": "string", "description": "Имя сотрудника"}}, "required": ["scenario_type"]}}},
]
