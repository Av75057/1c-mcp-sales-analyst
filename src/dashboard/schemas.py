from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class Axis(BaseModel):
    field: str
    label: str
    type: str  # time, category


class Series(BaseModel):
    name: str
    field: str
    color: str = "#5470c6"


class DrillDown(BaseModel):
    enabled: bool = False
    target_entity: str | None = None
    drill_fields: list[str] = []


class OnecQuery(BaseModel):
    entity: str
    fields: list[str]
    period: str = "last_30_days"
    aggregation: str = "sum"


class ChartConfig(BaseModel):
    chart_type: str = Field(default="bar", pattern="^(line|bar|pie)$")
    title: str = Field(default="", max_length=100)
    subtitle: str = Field(default="", max_length=200)
    x_axis: Axis
    y_axis: Axis
    series: list[Series] = Field(default_factory=list, min_length=1, max_length=10)
    filters: list[dict[str, Any]] = []
    group_by: list[str] = Field(default_factory=list, max_length=2)
    order_by: dict[str, str] = Field(default_factory=lambda: {"field": "", "direction": "desc"})
    limit: int = Field(default=50, ge=1, le=1000)
    drill_down: DrillDown = Field(default_factory=DrillDown)
    onec_query: OnecQuery


class DashboardRequest(BaseModel):
    query: str = Field(default="", min_length=1, max_length=500)
    session_id: str = ""


class DashboardResponse(BaseModel):
    status: str = "success"
    chart: ChartConfig | None = None
    data: list[dict[str, Any]] = []
    error_code: str = ""
    message: str = ""
    suggestions: list[str] = []
    meta: dict[str, Any] = Field(default_factory=dict)
