from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.insights.models import RawInsight, TenantInsightsConfig


class BaseDetector(ABC):
    def __init__(self, config: TenantInsightsConfig | None = None) -> None:
        self.config = config or TenantInsightsConfig()

    @abstractmethod
    async def detect(self, tenant_id: str = "default") -> list[RawInsight]:
        ...
