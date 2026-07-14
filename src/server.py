# START_MODULE_CONTRACT: mcp_server
# DESCRIPTION: MCP сервер (stdio транспорт) — регистрация и диспетчеризация инструментов
# DEPENDENCIES: src.tools, src.mcp.tools, src.clients.batch_client, src.mcp.documents_tool
# CONTRACTS: docs/requirements.xml
# END_MODULE_CONTRACT

from __future__ import annotations

import json
from typing import Any

from mcp.server import Server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

from src.logger import logger

server = Server("1c-mcp-sales-analyst")


# START_BLOCK_list_tools
# DESCRIPTION: Регистрация 7 базовых MCP инструментов
# INPUTS: нет
# OUTPUTS: ListToolsResult с описаниями tools
# SIDE_EFFECTS: read-only
# END_BLOCK_list_tools
@server.list_tools()
async def list_tools() -> ListToolsResult:
    tools = [
        Tool(
            name="get_stock",
            description="Получить остатки товаров на складах",
            inputSchema={
                "type": "object",
                "properties": {
                    "warehouse": {"type": "string", "description": "Название склада"},
                    "nomenclature": {"type": "string", "description": "Название номенклатуры"},
                    "min_quantity": {"type": "integer", "description": "Минимальное количество"},
                },
            },
        ),
        Tool(
            name="get_sales",
            description="Данные о продажах",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Начальная дата (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Конечная дата (YYYY-MM-DD)"},
                    "manager": {"type": "string", "description": "ФИО менеджера"},
                    "warehouse": {"type": "string", "description": "Название склада"},
                },
            },
        ),
        Tool(
            name="get_sales_by_manager",
            description="Продажи в разрезе менеджеров",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Начальная дата (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Конечная дата (YYYY-MM-DD)"},
                    "manager": {"type": "string", "description": "ФИО менеджера"},
                },
            },
        ),
        Tool(
            name="get_receivables",
            description="Задолженность клиентов",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_amount": {"type": "number", "description": "Минимальная сумма долга"},
                    "date_from": {"type": "string", "description": "Начальная дата (YYYY-MM-DD)"},
                },
            },
        ),
        Tool(
            name="list_nomenclature",
            description="Поиск номенклатуры",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос"},
                    "limit": {"type": "integer", "description": "Лимит результатов"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_analytics_context",
            description="Получить полный контекст для аналитики одним batch-запросом (итоги, топ товаров, топ клиентов, остатки, неликвиды)",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Начальная дата (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Конечная дата (YYYY-MM-DD)"},
                },
                "required": ["date_from", "date_to"],
            },
        ),
        Tool(
            name="get_sales_documents",
            description="Получить список документов реализации с номерами, датами, суммами и контрагентами",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Дата начала периода (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Дата окончания периода (YYYY-MM-DD)"},
                    "counterparty": {"type": "string", "description": "Фильтр по контрагенту"},
                    "sum_min": {"type": "number", "description": "Минимальная сумма"},
                    "sum_max": {"type": "number", "description": "Максимальная сумма"},
                    "page": {"type": "integer", "description": "Номер страницы"},
                    "page_size": {"type": "integer", "description": "Размер страницы"},
                },
                "required": ["date_from", "date_to"],
            },
        ),
    ]
    return ListToolsResult(tools=tools)


# START_BLOCK_call_tool
# DESCRIPTION: Диспетчеризация вызовов MCP инструментов
# INPUTS: name (str), arguments (dict)
# OUTPUTS: CallToolResult — json результат или ошибка
# SIDE_EFFECTS: зависит от инструмента (см. contracts в docs/requirements.xml)
# ERROR_HANDLING: все исключения перехватываются и возвращаются в isError=true
# END_BLOCK_call_tool
@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> CallToolResult:
    from src.tools import (
        get_receivables_tool,
        get_sales_by_manager_tool,
        get_sales_tool,
        get_stock_tool,
        list_nomenclature_tool,
    )

    tool_map = {
        "get_stock": get_stock_tool,
        "get_sales": get_sales_tool,
        "get_sales_by_manager": get_sales_by_manager_tool,
        "get_receivables": get_receivables_tool,
        "list_nomenclature": list_nomenclature_tool,
        "get_analytics_context": _get_analytics_context,
        "get_sales_documents": _get_sales_documents,
    }

    func = tool_map.get(name)
    if func is None:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Неизвестный инструмент: {name}")],
            isError=True,
        )

    args = arguments or {}
    logger.info("MCP вызов инструмента: {} args={}", name, args)

    try:
        result = await func(**args)
        text = json.dumps(result, ensure_ascii=False, default=str, indent=2)
        return CallToolResult(content=[TextContent(type="text", text=text)])
    except Exception as e:
        logger.error("Ошибка при выполнении {}: {}", name, e)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Ошибка: {e!s}")],
            isError=True,
        )


async def _get_sales_documents(
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
    from src.mcp.documents_tool import get_sales_documents
    return await get_sales_documents(
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


async def _get_analytics_context(date_from: str = "", date_to: str = "") -> dict[str, Any]:
    from src.clients.batch_client import BatchC1Client

    async with BatchC1Client() as batch:
        return await batch.get_analytics_context(
            date_from=date_from or None,
            date_to=date_to or None,
        )


async def run_server_stdio() -> None:
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read, write):
        logger.info("MCP сервер запущен (stdio транспорт)")
        await server.run(read, write, server.create_initialization_options())
