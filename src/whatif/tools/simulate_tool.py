from __future__ import annotations

from typing import Any

from src.logger import logger
from src.whatif.engine.simulator import WhatIfSimulator
from src.whatif.models import SimulationRequest

SIMULATE_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "simulate_scenario",
        "description": "Симулировать бизнес-сценарий 'Что если?' — изменение цены, закупки, открытие склада и т.д.",
        "parameters": {
            "type": "object",
            "properties": {
                "scenario_type": {
                    "type": "string",
                    "enum": ["price_change"],
                    "description": "Тип сценария: price_change — изменение цены",
                },
                "entity_type": {
                    "type": "string",
                    "enum": ["nomenclature", "category"],
                    "description": "Тип сущности",
                },
                "entity_name": {
                    "type": "string",
                    "description": "Название товара или категории",
                },
                "change_percent": {
                    "type": "number",
                    "description": "Процент изменения цены (положительный = рост)",
                },
                "period_days": {
                    "type": "integer",
                    "description": "Период прогноза в днях (по умолчанию 30)",
                },
            },
            "required": ["scenario_type", "entity_name", "change_percent"],
        },
    },
}


async def simulate_scenario_tool(
    scenario_type: str,
    entity_name: str,
    change_percent: float,
    entity_type: str = "nomenclature",
    period_days: int = 30,
) -> dict[str, Any]:
    logger.info("simulate_scenario: {} {} change={}%", scenario_type, entity_name, change_percent)

    request = SimulationRequest(
        scenario_type=scenario_type,
        entity_type=entity_type,
        entity_name=entity_name,
        parameters={"change_percent": change_percent, "period_days": period_days},
    )

    simulator = WhatIfSimulator()
    result = await simulator.simulate(request)

    if not result.baseline.volume:
        return {"error": result.recommendations[0] if result.recommendations else "Ошибка симуляции"}

    return {
        "title": f"Симуляция: {result.request.entity_name}",
        "baseline": {
            "revenue": result.baseline.revenue,
            "volume": result.baseline.volume,
            "avg_price": result.baseline.avg_price,
        },
        "projected": {
            "revenue": result.projected.revenue,
            "volume": result.projected.volume,
            "avg_price": result.projected.avg_price,
        },
        "delta": {
            "revenue_percent": round((result.delta.revenue / result.baseline.revenue) * 100, 1) if result.baseline.revenue else 0,
            "volume_percent": round((result.delta.volume / result.baseline.volume) * 100, 1) if result.baseline.volume else 0,
        },
        "financial_effect": {
            "additional_revenue": result.financial_effect.additional_revenue,
            "additional_margin": result.financial_effect.additional_margin,
        },
        "risks": [{"name": r.name, "probability": r.probability, "impact": r.impact} for r in result.risks],
        "recommendations": result.recommendations,
        "confidence": result.confidence,
        "confidence_interval": result.confidence_interval,
        "time_series": {
            "dates": result.time_series.dates,
            "baseline": result.time_series.baseline,
            "projected": result.time_series.projected,
        },
        "data_quality": {
            "history_months": result.data_quality.history_months,
            "data_points": result.data_quality.data_points,
            "model_used": result.data_quality.model_used,
        },
    }
