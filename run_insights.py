#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import signal
import sys

from src.config import settings
from src.insights.engine import InsightsEngine
from src.insights.models import TenantInsightsConfig
from src.insights.scheduler.scheduler import SimpleScheduler
from src.logger import logger


async def main() -> None:
    settings.validate()

    config = TenantInsightsConfig(
        telegram_chat_ids=os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if os.getenv("TELEGRAM_CHAT_IDS") else [],
    )

    engine = InsightsEngine(config)
    scheduler = SimpleScheduler()

    mode = sys.argv[1] if len(sys.argv) > 1 else "daemon"

    if mode == "scan":
        results = await engine.scan_all()
        print(f"Найдено и отправлено: {len(results)} инсайтов")
        return

    if mode == "digest":
        await engine.run_weekly_digest()
        return

    if mode == "once":
        results = await engine.scan_all()
        print(f"Найдено и отправлено: {len(results)} инсайтов")
        return

    # daemon mode
    scheduler.daily(config.daily_scan_hour, config.daily_scan_minute, engine.run_daily_scan, "daily_scan")
    scheduler.weekly(config.weekly_digest_day, config.weekly_digest_hour, config.weekly_digest_minute, engine.run_weekly_digest, "weekly_digest")

    logger.info("Insights daemon запущен. Расписание: daily {}:{:02d}, weekly day={} {}:{:02d}",
                config.daily_scan_hour, config.daily_scan_minute,
                config.weekly_digest_day, config.weekly_digest_hour, config.weekly_digest_minute)

    stop = asyncio.Future()
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_event_loop().add_signal_handler(s, lambda: stop.set_result(True))
        except NotImplementedError:
            pass

    try:
        await stop
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        logger.info("Insights daemon остановлен")


if __name__ == "__main__":
    asyncio.run(main())
