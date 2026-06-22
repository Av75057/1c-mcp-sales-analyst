from __future__ import annotations

from typing import Any

from src.clients.c1_client import C1Client
from src.clients.mock_c1_client import MockC1Client
from src.config import settings
from src.logger import logger

C1ClientProtocol = C1Client | MockC1Client


def _get_client() -> C1ClientProtocol:
    if settings.use_mock_data:
        logger.info("Используется MockC1Client (демо-режим)")
        return MockC1Client()
    logger.info("Используется C1Client (режим 1С)")
    return C1Client()


_client_instance: C1ClientProtocol | None = None


def get_client() -> C1ClientProtocol:
    global _client_instance
    if _client_instance is None:
        _client_instance = _get_client()
    return _client_instance


async def close_client() -> None:
    global _client_instance
    if _client_instance:
        await _client_instance.close()
        _client_instance = None


async def get_stock_tool(
    warehouse: str | None = None,
    nomenclature: str | None = None,
    min_quantity: int | None = None,
) -> list[dict[str, Any]]:
    logger.info("Вызов get_stock: warehouse={}, nomenclature={}, min_quantity={}", warehouse, nomenclature, min_quantity)
    client = get_client()
    return await client.get_stock(
        warehouse=warehouse,
        nomenclature=nomenclature,
        min_quantity=min_quantity,
    )


async def get_sales_tool(
    date_from: str | None = None,
    date_to: str | None = None,
    manager: str | None = None,
    warehouse: str | None = None,
) -> list[dict[str, Any]]:
    logger.info("Вызов get_sales: date_from={}, date_to={}, manager={}, warehouse={}", date_from, date_to, manager, warehouse)
    client = get_client()
    return await client.get_sales(
        date_from=date_from,
        date_to=date_to,
        manager=manager,
        warehouse=warehouse,
    )


async def get_sales_by_manager_tool(
    date_from: str | None = None,
    date_to: str | None = None,
    manager: str | None = None,
) -> list[dict[str, Any]]:
    logger.info("Вызов get_sales_by_manager: date_from={}, date_to={}, manager={}", date_from, date_to, manager)
    client = get_client()
    return await client.get_sales_by_manager(
        date_from=date_from,
        date_to=date_to,
        manager=manager,
    )


async def get_receivables_tool(
    min_amount: float | None = None,
    date_from: str | None = None,
) -> list[dict[str, Any]]:
    logger.info("Вызов get_receivables: min_amount={}, date_from={}", min_amount, date_from)
    client = get_client()
    return await client.get_receivables(
        min_amount=min_amount,
        date_from=date_from,
    )


async def list_nomenclature_tool(
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    logger.info("Вызов list_nomenclature: query={}, limit={}", query, limit)
    client = get_client()
    return await client.list_nomenclature(query=query, limit=limit)


async def get_purchases_tool(
    date_from: str | None = None,
    date_to: str | None = None,
    item: str | None = None,
    supplier: str | None = None,
) -> list[dict[str, Any]]:
    logger.info("get_purchases: date_from={}, date_to={}, item={}, supplier={}", date_from, date_to, item, supplier)
    client = get_client()
    return await client.get_purchases(
        date_from=date_from,
        date_to=date_to,
        item=item,
        supplier=supplier,
    )


async def create_chart_tool(
    chart_type: str,
    title: str,
    x_data: list[Any],
    y_data: list[Any],
    x_label: str = "",
    y_label: str = "",
    series_names: list[str] | None = None,
    color_scheme: str = "default",
) -> dict[str, Any]:
    logger.info("create_chart: type={}, title={}, points={}", chart_type, title, len(x_data))
    from src.charts.tool import create_chart_tool as _create
    return _create(
        chart_type=chart_type,
        title=title,
        x_data=x_data,
        y_data=y_data,
        x_label=x_label,
        y_label=y_label,
        series_names=series_names,
        color_scheme=color_scheme,
    )


async def simulate_scenario_tool(
    scenario_type: str,
    entity_name: str = "",
    change_percent: float | None = None,
    discount_percent: float | None = None,
    period_days: int = 30,
    promotion_days: int | None = None,
    order_size_change_percent: float | None = None,
    employee_name: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    logger.info("simulate_scenario: type={}, entity={}", scenario_type, entity_name)
    from src.whatif.mcp.tools import simulate_scenario_tool as _sim
    return await _sim(
        scenario_type=scenario_type,
        entity_name=entity_name,
        change_percent=change_percent,
        discount_percent=discount_percent,
        period_days=period_days,
        promotion_days=promotion_days,
        order_size_change_percent=order_size_change_percent,
        employee_name=employee_name or entity_name,
    )


async def abc_xyz_analysis_tool(
    date_from: str = "",
    date_to: str = "",
    group_by: str = "nomenclature",
    abc_thresholds: list[int] | None = None,
    xyz_thresholds: list[int] | None = None,
) -> dict[str, Any]:
    logger.info("abc_xyz_analysis: {}-{}", date_from, date_to)
    from src.analysis.tool import abc_xyz_analysis_tool as _a
    return await _a(date_from=date_from, date_to=date_to, group_by=group_by, abc_thresholds=abc_thresholds, xyz_thresholds=xyz_thresholds)
