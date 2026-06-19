from __future__ import annotations

import asyncio
from datetime import datetime, time, timedelta
from typing import Any, Callable, Coroutine

from src.logger import logger

JobFunc = Callable[[], Coroutine[Any, Any, None]]


class SimpleScheduler:
    def __init__(self) -> None:
        self._tasks: list[asyncio.Task[Any]] = []

    def daily(self, hour: int, minute: int, func: JobFunc, name: str = "") -> None:
        async def loop() -> None:
            while True:
                now = datetime.now()
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                delay = (target - now).total_seconds()
                logger.info("Scheduler [{}]: следующий запуск через {:.1f}ч", name or func.__name__, delay / 3600)
                await asyncio.sleep(delay)
                try:
                    logger.info("Scheduler [{}]: запуск", name or func.__name__)
                    await func()
                except Exception as e:
                    logger.error("Scheduler [{}]: ошибка: {}", name or func.__name__, e)

        task = asyncio.create_task(loop(), name=name or func.__name__)
        self._tasks.append(task)
        logger.info("Scheduler: добавлена задача daily {}:{:02d} {}", hour, minute, name or func.__name__)

    def weekly(self, day_of_week: int, hour: int, minute: int, func: JobFunc, name: str = "") -> None:
        async def loop() -> None:
            while True:
                now = datetime.now()
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                days_ahead = (day_of_week - now.weekday() + 7) % 7
                if days_ahead == 0 and target <= now:
                    days_ahead = 7
                target += timedelta(days=days_ahead)
                delay = (target - now).total_seconds()
                logger.info("Scheduler [{}]: следующий запуск через {:.1f}ч (день недели {})", name or func.__name__, delay / 3600, day_of_week)
                await asyncio.sleep(delay)
                try:
                    logger.info("Scheduler [{}]: запуск", name or func.__name__)
                    await func()
                except Exception as e:
                    logger.error("Scheduler [{}]: ошибка: {}", name or func.__name__, e)

        task = asyncio.create_task(loop(), name=name or func.__name__)
        self._tasks.append(task)
        logger.info("Scheduler: добавлена задача weekly day={} {}:{:02d} {}", day_of_week, hour, minute, name or func.__name__)

    def interval(self, seconds: float, func: JobFunc, name: str = "") -> None:
        async def loop() -> None:
            while True:
                await asyncio.sleep(seconds)
                try:
                    await func()
                except Exception as e:
                    logger.error("Scheduler [{}]: ошибка: {}", name or func.__name__, e)

        task = asyncio.create_task(loop(), name=name or func.__name__)
        self._tasks.append(task)
        logger.info("Scheduler: добавлена задача interval {}с {}", seconds, name or func.__name__)

    def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("Scheduler: остановлен")
