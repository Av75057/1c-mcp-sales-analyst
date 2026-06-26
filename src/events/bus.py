from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Callable

from src.logger import logger


class Event:
    def __init__(self, event_type: str, data: dict[str, Any] | None = None, source: str = "", user_id: str | None = None):
        self.id = str(uuid.uuid4())[:8]
        self.type = event_type
        self.data = data or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.source = source
        self.user_id = user_id


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
        self._dead_letter: list[Event] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info("[EventBus] Subscribed to {}: {}", event_type, handler.__name__)

    def subscribe_all(self, handlers: dict[str, list[Callable]]) -> None:
        for event_type, handler_list in handlers.items():
            for handler in handler_list:
                self.subscribe(event_type, handler)

    async def publish(self, event: Event) -> None:
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                await handler(event)
                logger.debug("[EventBus] {} handled by {}", event.type, handler.__name__)
            except Exception as e:
                logger.error("[EventBus] Handler {} failed for {}: {}", handler.__name__, event.type, e)
                self._dead_letter.append(event)

    def get_dead_letter(self) -> list[dict[str, Any]]:
        return [{"id": e.id, "type": e.type, "data": e.data, "source": e.source, "timestamp": e.timestamp} for e in self._dead_letter]

    async def replay_dead_letter(self) -> int:
        count = 0
        for event in list(self._dead_letter):
            try:
                await self.publish(event)
                self._dead_letter.remove(event)
                count += 1
            except Exception:
                pass
        return count


event_bus = EventBus()
