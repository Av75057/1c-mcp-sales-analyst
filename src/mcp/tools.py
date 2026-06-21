from __future__ import annotations

from typing import Any

from src.logger import logger
from src.tools import (
    create_chart_tool,
    get_receivables_tool,
    get_sales_by_manager_tool,
    get_sales_tool,
    get_stock_tool,
    list_nomenclature_tool,
)
from src.whatif.mcp.tools import WHATIF_TOOLS_SCHEMA, list_whatif_scenarios_tool, simulate_scenario_tool

EXISTING_TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "get_stock", "description": "Получить остатки товаров", "parameters": {"type": "object", "properties": {"warehouse": {"type": "string"}, "nomenclature": {"type": "string"}, "min_quantity": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_sales", "description": "Получить данные о продажах", "parameters": {"type": "object", "properties": {"date_from": {"type": "string"}, "date_to": {"type": "string"}, "manager": {"type": "string"}}, "required": ["date_from", "date_to"]}}},
    {"type": "function", "function": {"name": "get_sales_by_manager", "description": "Продажи по менеджерам", "parameters": {"type": "object", "properties": {"date_from": {"type": "string"}, "date_to": {"type": "string"}, "manager": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_receivables", "description": "Задолженность клиентов", "parameters": {"type": "object", "properties": {"min_amount": {"type": "number"}, "date_from": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "list_nomenclature", "description": "Поиск номенклатуры", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "create_chart", "description": "Построить график", "parameters": {"type": "object", "properties": {"chart_type": {"type": "string", "enum": ["line", "bar", "hbar", "pie", "area"]}, "title": {"type": "string"}, "x_data": {"type": "array"}, "y_data": {"type": "array"}, "x_label": {"type": "string"}, "y_label": {"type": "string"}, "series_names": {"type": "array"}, "color_scheme": {"type": "string", "enum": ["default", "corporate", "vibrant"]}}, "required": ["chart_type", "title", "x_data", "y_data"]}}},
]

ALL_TOOLS_SCHEMA = EXISTING_TOOLS_SCHEMA + WHATIF_TOOLS_SCHEMA

TOOLS_REGISTRY: dict[str, Any] = {
    "get_stock": get_stock_tool,
    "get_sales": get_sales_tool,
    "get_sales_by_manager": get_sales_by_manager_tool,
    "get_receivables": get_receivables_tool,
    "list_nomenclature": list_nomenclature_tool,
    "create_chart": create_chart_tool,
    "simulate_scenario": simulate_scenario_tool,
    "list_whatif_scenarios": list_whatif_scenarios_tool,
}


def get_tool_function(tool_name: str) -> Any:
    if tool_name not in TOOLS_REGISTRY:
        raise ValueError(f"Неизвестный tool: {tool_name}. Доступны: {list(TOOLS_REGISTRY.keys())}")
    return TOOLS_REGISTRY[tool_name]


def list_all_tools() -> list[str]:
    return list(TOOLS_REGISTRY.keys())
