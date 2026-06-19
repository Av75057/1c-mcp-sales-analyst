from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

from src.config import settings
from src.insights.deduplication.dedup_engine import DedupEngine
from src.insights.delivery.telegram import TelegramDelivery
from src.insights.detectors.inactive_clients import InactiveClientsDetector
from src.insights.detectors.receivables_alert import ReceivablesAlertDetector
from src.insights.detectors.sales_anomaly import SalesAnomalyDetector
from src.insights.detectors.sales_growth import SalesGrowthDetector
from src.insights.detectors.stock_shortage import StockShortageDetector
from src.insights.interpreter.llm_interpreter import LLMInterpreter
from src.insights.models import ProcessedInsight, RawInsight, TenantInsightsConfig
from src.logger import logger


class InsightsEngine:
    def __init__(self, config: TenantInsightsConfig | None = None) -> None:
        self.config = config or TenantInsightsConfig()
        self.dedup = DedupEngine(self.config)
        self.interpreter = LLMInterpreter()
        self.telegram: TelegramDelivery | None = None

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if bot_token and self.config.telegram_chat_ids:
            self.telegram = TelegramDelivery(bot_token, self.config.telegram_chat_ids)
        else:
            logger.info("Telegram не настроен (TELEGRAM_BOT_TOKEN или chat_ids)")

        self.detectors: list[Any] = [
            SalesAnomalyDetector(self.config),
            SalesGrowthDetector(self.config),
            StockShortageDetector(self.config),
            InactiveClientsDetector(self.config),
            ReceivablesAlertDetector(self.config),
        ]

    async def scan_all(self, tenant_id: str = "default") -> list[ProcessedInsight]:
        logger.info("=== InsightsEngine: полный скан ===")

        all_raws: list[RawInsight] = []
        for detector in self.detectors:
            try:
                raws = await detector.detect(tenant_id=tenant_id)
                all_raws.extend(raws)
            except Exception as e:
                logger.error("Ошибка детектора {}: {}", detector.__class__.__name__, e)

        if not all_raws:
            logger.info("InsightsEngine: нет новых инсайтов")
            return []

        new_raws = [r for r in all_raws if self.dedup.should_send(r)]
        logger.info("InsightsEngine: {} сырых, {} новых после дедупликации", len(all_raws), len(new_raws))

        processed = await self.interpreter.interpret_batch(new_raws)

        for p in processed:
            self.dedup.mark_sent(p.raw)
            if self.telegram:
                await self.telegram.send_insight(p)

        return processed

    async def run_daily_scan(self) -> None:
        logger.info("=== Ежедневный скан ===")
        await self.scan_all()

    async def run_weekly_digest(self) -> None:
        logger.info("=== Еженедельный дайджест ===")
        results = await self.scan_all()
        if results:
            lines = ["📊 **Еженедельный дайджест**\n", f"Период: {date.today() - timedelta(days=7)} — {date.today()}\n"]
            for p in results:
                lines.append(f"• {p.llm_title}")
            digest = "\n".join(lines)
            if self.telegram:
                for chat_id in self.config.telegram_chat_ids:
                    import httpx
                    async with httpx.AsyncClient() as c:
                        await c.post(
                            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN', '')}/sendMessage",
                            json={"chat_id": chat_id, "text": digest, "parse_mode": "Markdown"},
                        )
            logger.info("Дайджест отправлен")
