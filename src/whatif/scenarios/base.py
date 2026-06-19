from __future__ import annotations

from abc import ABC, abstractmethod

from src.whatif.models import SimulationRequest, SimulationResult


class BaseScenarioHandler(ABC):
    @abstractmethod
    async def execute(self, request: SimulationRequest) -> SimulationResult:
        ...
