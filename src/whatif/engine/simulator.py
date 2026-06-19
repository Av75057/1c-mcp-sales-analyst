from __future__ import annotations

from src.logger import logger
from src.whatif.models import SimulationRequest, SimulationResult
from src.whatif.scenarios.price_change import PriceChangeScenario


class WhatIfSimulator:
    async def simulate(self, request: SimulationRequest) -> SimulationResult:
        logger.info("Simulator: сценарий {} для {}", request.scenario_type, request.entity_name)

        handlers = {
            "price_change": PriceChangeScenario(),
        }

        handler = handlers.get(request.scenario_type)
        if not handler:
            return SimulationResult(
                request=request,
                confidence=0.0,
                recommendations=[f"Сценарий '{request.scenario_type}' пока не реализован"],
            )

        result = await handler.execute(request)
        return result
