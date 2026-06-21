from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScenarioResult:
    scenario_type: str = ""
    scenario_name: str = ""
    entity_name: str = ""
    baseline_metrics: dict[str, float] = field(default_factory=dict)
    projected_metrics: dict[str, float] = field(default_factory=dict)
    delta_metrics: dict[str, float] = field(default_factory=dict)
    delta_percent: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    confidence_interval: tuple[float, float] | None = None
    risks: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    additional_data: dict[str, Any] = field(default_factory=dict)
    formatted_summary: str = ""


class BaseScenario(ABC):
    def __init__(self) -> None:
        self.scenario_type: str = ""
        self.scenario_name: str = ""

    @abstractmethod
    def simulate(self, **kwargs: Any) -> ScenarioResult:
        ...
