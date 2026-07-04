from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class Axis(BaseModel):
    field: str
    label: str
    type: str  # time, category, value


class Series(BaseModel):
    name: str
    field: str
    color: str = "#5470c6"
    type: str | None = None  # bar, line for combo charts


class DrillDown(BaseModel):
    enabled: bool = False
    target_entity: str | None = None
    drill_fields: list[str] = []


class OnecQuery(BaseModel):
    entity: str
    fields: list[str]
    period: str = "last_30_days"
    aggregation: str = "sum"
    date_from: str | None = None
    date_to: str | None = None


class ColorRange(BaseModel):
    min: float = 0
    max: float = 100
    color: str = "#5470c6"


class HeatmapConfig(BaseModel):
    x_field: str
    y_field: str
    value_field: str
    color_ranges: list[ColorRange] = [ColorRange(min=0, max=50, color="#91cc75"), ColorRange(min=50, max=100, color="#fac858"), ColorRange(min=100, max=999999, color="#ee6666")]


class TreemapConfig(BaseModel):
    category_field: str
    value_field: str
    max_depth: int = 2


class SankeyConfig(BaseModel):
    source_field: str
    target_field: str
    value_field: str


class GaugeConfig(BaseModel):
    value_field: str
    min: float = 0
    max: float = 100
    target: float | None = None


class RadarConfig(BaseModel):
    dimensions: list[str] = Field(default_factory=list, min_length=3, max_length=12)
    value_field: str


class ChartConfig(BaseModel):
    chart_type: str = Field(default="bar", pattern="^(line|bar|pie|horizontal_bar|area|combo|scatter|heatmap|treemap|sankey|gauge|radar)$")
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
    heatmap: HeatmapConfig | None = None
    treemap: TreemapConfig | None = None
    sankey: SankeyConfig | None = None
    gauge: GaugeConfig | None = None
    radar: RadarConfig | None = None


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


# --- Composite Dashboard (multi-chart) ---

class ChartItem(BaseModel):
    id: str = ""
    title: str = ""
    chart_config: ChartConfig
    data: list[dict[str, Any]] = []
    position: dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0, "w": 6, "h": 4})
    filter_bindings: list[str] = []  # fields that can be cross-filtered


class CompositeDashboardCreate(BaseModel):
    title: str = Field(default="", max_length=200)
    description: str = ""
    charts: list[ChartItem] = Field(default_factory=list, min_length=1, max_length=12)
    tags: list[str] = []
    is_public: bool = False
    refresh_interval_minutes: int = 0  # 0 = no auto-refresh


class CompositeDashboard(CompositeDashboardCreate):
    id: str
    owner_id: str
    created_at: str
    updated_at: str
    view_count: int = 0


class CompositeDashboardListResponse(BaseModel):
    status: str = "success"
    dashboards: list[CompositeDashboard] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    total_pages: int = 1


# --- RBAC ---

class DashboardPermission(BaseModel):
    dashboard_id: str
    user_id: str
    permission: str = "view"  # view, edit, admin


class DashboardShareRequest(BaseModel):
    user_id: str
    permission: str = "view"


# --- Scheduler ---

class ScheduledReport(BaseModel):
    id: str = ""
    dashboard_id: str
    owner_id: str
    cron: str = "0 9 * * 1"  # default: Monday 9 AM
    recipients: list[str] = Field(default_factory=list)
    format: str = "csv"  # csv, xlsx, pdf
    is_active: bool = True
    last_run: str | None = None
    next_run: str | None = None
    created_at: str = ""


class ScheduledReportCreate(BaseModel):
    dashboard_id: str
    cron: str = "0 9 * * 1"
    recipients: list[str] = Field(default_factory=list)
    format: str = "csv"


# --- Notifications ---

class Notification(BaseModel):
    id: str = ""
    dashboard_id: str
    user_id: str
    type: str = "anomaly"  # anomaly, refresh_done, report_ready
    title: str
    message: str
    is_read: bool = False
    created_at: str = ""


# --- Recommendations ---

class DashboardRecommendation(BaseModel):
    dashboard_id: str
    title: str
    description: str
    confidence: float = 0.5
    reason: str = ""
    suggested_action: str = ""
