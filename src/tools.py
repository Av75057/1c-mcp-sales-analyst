# START_MODULE_CONTRACT: mcp_tools_factory
# DESCRIPTION: Фабрика MCP инструментов — адаптеры между MCP-вызовами и бизнес-логикой
# DEPENDENCIES: src.clients.*, src.cache, src.config, src.analysis, src.forecasting, src.charts, src.whatif, src.metadata
# CONTRACTS: docs/requirements.xml
# NOTE: C1ClientProtocol — синглтон, ленивая инициализация
# END_MODULE_CONTRACT

from __future__ import annotations

from typing import Any

from typing import Literal

from src.cache import CachedC1Client
from src.clients.c1_client import C1Client
from src.clients.mock_c1_client import MockC1Client
from src.config import settings
from src.logger import logger
from src.perf import measure_time

C1ClientProtocol = C1Client | MockC1Client | CachedC1Client


def _get_client() -> C1ClientProtocol:
    if settings.use_mock_data:
        logger.info("Используется MockC1Client (демо-режим)")
        return MockC1Client()
    logger.info("Используется CachedC1Client (режим 1С)")
    return CachedC1Client(C1Client(), ttl=30)


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


# START_BLOCK_get_stock_tool
# CONTRACT: docs/requirements.xml#get_stock
# END_BLOCK_get_stock_tool
@measure_time("get_stock")
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


# START_BLOCK_get_sales_tool
# CONTRACT: docs/requirements.xml#get_sales
# END_BLOCK_get_sales_tool
@measure_time("get_sales")
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


# START_BLOCK_get_sales_by_manager_tool
# CONTRACT: docs/requirements.xml#get_sales_by_manager
# END_BLOCK_get_sales_by_manager_tool
@measure_time("get_sales_by_manager")
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


# START_BLOCK_get_receivables_tool
# CONTRACT: docs/requirements.xml#get_receivables
# END_BLOCK_get_receivables_tool
@measure_time("get_receivables")
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


@measure_time("list_nomenclature")
async def list_nomenclature_tool(
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    logger.info("Вызов list_nomenclature: query={}, limit={}", query, limit)
    client = get_client()
    return await client.list_nomenclature(query=query, limit=limit)


@measure_time("get_purchases")
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


async def forecast_sales_tool(nomenclature: str, days: int = 30, method: str = "auto") -> dict[str, Any]:
    logger.info("forecast_sales: {} {} days", nomenclature, days)
    from src.forecasting.tool import forecast_sales_tool as _f
    return await _f(nomenclature=nomenclature, days=days, method=method)


async def forecast_stockout_tool(lead_time_days: int = 7, safety_stock_days: int = 3) -> dict[str, Any]:
    logger.info("forecast_stockout: lead={}", lead_time_days)
    from src.forecasting.tool import forecast_stockout_tool as _f
    return await _f(lead_time_days=lead_time_days, safety_stock_days=safety_stock_days)


async def compare_forecasts_tool(nomenclature: str, test_days: int = 14) -> dict[str, Any]:
    logger.info("compare_forecasts: {} test_days={}", nomenclature, test_days)
    from src.forecasting.tool import compare_forecasts_tool as _c
    return await _c(nomenclature=nomenclature, test_days=test_days)


@measure_time("get_sales_documents")
async def get_sales_documents_tool(
    date_from: str = "",
    date_to: str = "",
    counterparty: str | None = None,
    sum_min: float | None = None,
    sum_max: float | None = None,
    posted_only: bool = True,
    sort_by: str = "date",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """Получить список документов реализации с номерами, датами, суммами."""
    logger.info(
        "Вызов get_sales_documents: {}-{} counterparty={} page={}",
        date_from, date_to, counterparty, page,
    )
    from src.mcp.documents_tool import get_sales_documents as _doc
    return await _doc(
        date_from=date_from,
        date_to=date_to,
        counterparty=counterparty,
        sum_min=sum_min,
        sum_max=sum_max,
        posted_only=posted_only,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@measure_time("get_analytics_context")
@measure_time("config")
async def config_tool() -> dict:
    """Паспорт базы 1С."""
    from src.metadata.service import metadata_service
    return await metadata_service.get_config()


@measure_time("describe")
async def describe_tool(object_type: str | None = None, search: str | None = None) -> dict:
    """Список объектов метаданных."""
    from src.metadata.service import metadata_service
    objects = await metadata_service.describe(object_type=object_type, search=search)
    return {"objects": objects, "total": len(objects)}


@measure_time("get_structure")
async def get_structure_tool(object_name: str) -> dict:
    """Структура объекта метаданных."""
    from src.metadata.service import metadata_service
    return await metadata_service.get_structure(object_name)


@measure_time("get_analytics_context")
async def get_analytics_context_tool(
    date_from: str = "",
    date_to: str = "",
) -> dict[str, Any]:
    """Получить полный контекст для AI-аналитики одним batch-запросом."""
    logger.info("Вызов get_analytics_context: date_from={}, date_to={}", date_from, date_to)
    from src.clients.batch_client import BatchC1Client

    async with BatchC1Client() as batch:
        return await batch.get_analytics_context(
            date_from=date_from or None,
            date_to=date_to or None,
        )


@measure_time("generate_executive_summary")
async def generate_executive_summary_tool(
    period: str = "today",
    organization: str | None = None,
    include_sparklines: bool = True,
) -> dict[str, Any]:
    """Сгенерировать AI-сводку для руководителя на основе KPI-данных."""
    from src.mcp.summary_generator import generate_executive_summary

    from src.mcp.kpi_dashboard import get_executive_kpi
    kpi = await get_executive_kpi(period=period, organization=organization, include_sparklines=include_sparklines)
    return await generate_executive_summary(
        period=period,
        kpi_data=kpi.model_dump(mode="json"),
        organization=organization,
    )


@measure_time("get_executive_kpi")
async def get_executive_kpi_tool(
    period: Literal["today", "yesterday", "this_week", "last_week", "this_month", "last_month", "this_quarter", "this_year"] = "today",
    organization: str | None = None,
    include_sparklines: bool = True,
) -> dict[str, Any]:
    """Получить KPI для панели руководителя (выручка, прибыль, заказы, маржа, топ-менеджер)."""
    logger.info("Вызов get_executive_kpi: period={}, org={}, sparklines={}", period, organization, include_sparklines)
    from src.mcp.kpi_dashboard import get_executive_kpi
    result = await get_executive_kpi(
        period=period,
        organization=organization,
        include_sparklines=include_sparklines,
    )
    return result.model_dump(mode="json")
