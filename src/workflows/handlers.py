from __future__ import annotations

from src.events.bus import Event
from src.logger import logger


async def notify_stock_manager(event: Event) -> None:
    data = event.data
    logger.info("[Workflow] notify_stock_manager: {} (qty={})", data.get("nomenclature_name", "?"), data.get("quantity", "?"))
    # In production: send to Telegram


async def create_purchase_order(event: Event) -> None:
    data = event.data
    order_qty = data.get("min_qty", 10) * 2 - data.get("quantity", 0)
    logger.info("[Workflow] create_purchase_order: {} qty={}", data.get("nomenclature_id", "?"), order_qty)


async def notify_purchase_created(event: Event) -> None:
    logger.info("[Workflow] notify_purchase_created: order created for {}", event.data.get("nomenclature_name", "?"))


async def notify_sales_anomaly(event: Event) -> None:
    logger.info("[Workflow] notify_sales_anomaly: {}", event.data.get("type", "?"))
