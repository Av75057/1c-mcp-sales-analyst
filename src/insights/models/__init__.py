from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from typing import Any


class Priority(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class InsightStatus(str, Enum):
    NEW = "new"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


@dataclass
class RawInsight:
    detector: str
    priority: Priority
    title: str
    entity_type: str
    entity_id: str
    entity_name: str
    metric_name: str
    metric_value: float
    metric_baseline: float
    metric_delta_percent: float
    period_from: date
    period_to: date
    context: dict[str, Any] = field(default_factory=dict)
    id: str = ""
    tenant_id: str = "default"
    detected_at: datetime = field(default_factory=lambda: datetime.now())
    dedup_key: str = ""

    def __post_init__(self) -> None:
        if not self.dedup_key:
            iso = self.period_to.isocalendar()
            self.dedup_key = f"{self.detector}:{self.entity_type}:{self.entity_id}:{self.metric_name}:{iso[0]}:{iso[1]}"


@dataclass
class ProcessedInsight:
    raw: RawInsight
    llm_title: str = ""
    llm_summary: str = ""
    llm_hypothesis: str = ""
    llm_recommendations: list[str] = field(default_factory=list)
    formatted_message: str = ""
    status: InsightStatus = InsightStatus.NEW
    id: str = ""
    sent_at: datetime | None = None
    resolved_at: datetime | None = None

    @property
    def priority(self) -> Priority:
        return self.raw.priority


@dataclass
class TenantInsightsConfig:
    tenant_id: str = "default"
    enabled: bool = True
    timezone: str = "Europe/Moscow"

    daily_scan_hour: int = 9
    daily_scan_minute: int = 0
    weekly_digest_day: int = 6
    weekly_digest_hour: int = 18
    weekly_digest_minute: int = 0

    telegram_chat_ids: list[str] = field(default_factory=list)
    email_recipients: list[str] = field(default_factory=list)
    webhook_urls: list[str] = field(default_factory=list)

    sales_drop_threshold: float = 0.30
    sales_growth_threshold: float = 0.25
    inactive_days_multiplier: float = 2.0
    receivables_growth_threshold: float = 0.20
    stock_days_threshold: int = 7
    price_change_threshold: float = 0.15

    silence_period_hours: dict[str, int] = field(default_factory=lambda: {
        "critical": 24,
        "warning": 168,
        "info": 336,
    })

    routing_rules: list[dict[str, Any]] = field(default_factory=list)


DEFAULT_CONFIG = TenantInsightsConfig()
