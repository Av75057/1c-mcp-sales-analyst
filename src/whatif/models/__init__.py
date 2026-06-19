from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class SimulationRequest:
    scenario_type: str
    entity_type: str
    entity_name: str
    entity_id: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    tenant_id: str = "default"


@dataclass
class ScenarioMetrics:
    revenue: float = 0.0
    margin: float = 0.0
    volume: float = 0.0
    avg_price: float = 0.0

    def __sub__(self, other: "ScenarioMetrics") -> "ScenarioMetrics":
        return ScenarioMetrics(
            revenue=self.revenue - other.revenue,
            margin=self.margin - other.margin,
            volume=self.volume - other.volume,
            avg_price=self.avg_price - other.avg_price,
        )


@dataclass
class FinancialEffect:
    additional_revenue: float = 0.0
    additional_margin: float = 0.0
    costs: float = 0.0
    roi_percent: float = 0.0
    payback_months: float = 0.0


@dataclass
class Risk:
    name: str = ""
    probability: float = 0.0
    impact: str = ""
    mitigation: str = ""


@dataclass
class TimeSeries:
    dates: list[str] = field(default_factory=list)
    baseline: list[float] = field(default_factory=list)
    projected: list[float] = field(default_factory=list)
    projected_low: list[float] = field(default_factory=list)
    projected_high: list[float] = field(default_factory=list)


@dataclass
class DataQuality:
    history_months: int = 0
    data_points: int = 0
    seasonality_detected: bool = False
    model_used: str = ""


@dataclass
class SimulationResult:
    request: SimulationRequest
    baseline: ScenarioMetrics = field(default_factory=ScenarioMetrics)
    projected: ScenarioMetrics = field(default_factory=ScenarioMetrics)
    delta: ScenarioMetrics = field(default_factory=ScenarioMetrics)
    financial_effect: FinancialEffect = field(default_factory=FinancialEffect)
    risks: list[Risk] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    confidence_interval: dict[str, float] = field(default_factory=lambda: {"revenue_low": 0, "revenue_high": 0})
    time_series: TimeSeries = field(default_factory=TimeSeries)
    data_quality: DataQuality = field(default_factory=DataQuality)
    created_at: datetime = field(default_factory=datetime.now)
    simulation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        import json
        return json.loads(json.dumps(self, default=str, ensure_ascii=False))
