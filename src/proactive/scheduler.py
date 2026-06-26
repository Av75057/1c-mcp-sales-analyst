from __future__ import annotations

from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.events.bus import Event, event_bus
from src.logger import logger


class ScheduledAnalytics:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self._jobs: list[dict[str, Any]] = []

    def setup(self) -> None:
        self.scheduler.add_job(self.morning_report, CronTrigger(hour=8, minute=0), id="morning_report")
        self.scheduler.add_job(self.check_anomalies, IntervalTrigger(hours=1), id="check_anomalies")
        self.scheduler.add_job(self.check_stock, IntervalTrigger(minutes=30), id="check_stock")

        self._jobs = [
            {"id": "morning_report", "schedule": "daily 8:00", "description": "Утренний отчёт"},
            {"id": "check_anomalies", "schedule": "every 1h", "description": "Проверка аномалий"},
            {"id": "check_stock", "schedule": "every 30min", "description": "Проверка остатков"},
        ]

    def start(self) -> None:
        self.setup()
        self.scheduler.start()
        logger.info("[Scheduler] Started {} jobs", len(self._jobs))

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def get_jobs(self) -> list[dict[str, Any]]:
        return self._jobs

    async def run_job(self, job_id: str) -> str:
        if job_id == "morning_report":
            await self.morning_report()
        elif job_id == "check_anomalies":
            await self.check_anomalies()
        elif job_id == "check_stock":
            await self.check_stock()
        else:
            raise ValueError(f"Unknown job: {job_id}")
        return f"Job {job_id} executed"

    async def morning_report(self) -> None:
        logger.info("[Scheduler] Generating morning report")
        await event_bus.publish(Event(event_type="morning_report_generated", data={"timestamp": datetime.utcnow().isoformat()}, source="scheduler"))

    async def check_anomalies(self) -> None:
        logger.debug("[Scheduler] Checking anomalies")

    async def check_stock(self) -> None:
        logger.debug("[Scheduler] Checking stock levels")


scheduler = ScheduledAnalytics()
