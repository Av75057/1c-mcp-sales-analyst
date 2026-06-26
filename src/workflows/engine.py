from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable

from src.events.bus import Event, EventBus
from src.logger import logger
from src.workflows.models import Workflow, WorkflowStep


class WorkflowEngine:
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.workflows: dict[str, Workflow] = {}
        self.execution_log: list[dict[str, Any]] = []

    def register(self, workflow: Workflow) -> None:
        self.workflows[workflow.name] = workflow
        for step in workflow.steps:
            self.event_bus.subscribe(step.event_type, self._create_handler(workflow, step))
        logger.info("[Workflow] Registered: {} ({} steps)", workflow.name, len(workflow.steps))

    def _create_handler(self, workflow: Workflow, step: WorkflowStep) -> Callable:
        async def handler(event: Event) -> None:
            if step.condition:
                try:
                    if not eval(step.condition, {"event": event, "data": event.data}):
                        return
                except Exception as e:
                    logger.error("[Workflow] Condition failed: {}", e)
                    return
            try:
                from src.workflows.handlers import notify_stock_manager, create_purchase_order, notify_purchase_created, notify_sales_anomaly
                handler_map = {
                    "notify_stock_manager": notify_stock_manager,
                    "create_purchase_order": create_purchase_order,
                    "notify_purchase_created": notify_purchase_created,
                    "notify_sales_anomaly": notify_sales_anomaly,
                }
                func = handler_map.get(step.handler)
                if func:
                    await asyncio.wait_for(func(event), timeout=step.timeout_seconds)
                    self.execution_log.append({"workflow": workflow.name, "step": step.name, "event_id": event.id, "status": "success", "timestamp": datetime.utcnow().isoformat()})
                    if step.next_step:
                        next_s = next(s for s in workflow.steps if s.name == step.next_step)
                        await self.event_bus.publish(Event(event_type=next_s.event_type, data=event.data, source=f"workflow:{workflow.name}", user_id=event.user_id))
            except Exception as e:
                logger.error("[Workflow] Step failed: {}.{}: {}", workflow.name, step.name, e)
                self.execution_log.append({"workflow": workflow.name, "step": step.name, "event_id": event.id, "status": "failed", "error": str(e), "timestamp": datetime.utcnow().isoformat()})
        return handler

    def get_status(self) -> list[dict[str, Any]]:
        return [{"name": w.name, "steps": len(w.steps), "is_active": w.is_active, "description": w.description} for w in self.workflows.values()]
