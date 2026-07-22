# START_MODULE_CONTRACT: mcp_tools_registry
# DESCRIPTION: Реестр всех MCP инструментов для proxy_server.py
# DEPENDENCIES: src.tools, src.whatif.mcp.tools
# TOOLS: 19 инструментов (data + analytics + whatif + viz + metadata)
# END_MODULE_CONTRACT

from __future__ import annotations

from typing import Any

from src.logger import logger
from src.tools import (
    abc_xyz_analysis_tool,
    compare_forecasts_tool,
    config_tool,
    create_chart_tool,
    describe_tool,
    drill_down_tool,
    forecast_sales_tool,
    forecast_stockout_tool,
    generate_executive_summary_tool,
    get_analytics_context_tool,
    get_executive_kpi_tool,
    get_purchases_tool,
    get_receivables_tool,
    get_sales_tool,
    get_sales_by_manager_tool,
    get_sales_documents_tool,
    get_stock_tool,
    get_structure_tool,
    list_nomenclature_tool,
)
from src.whatif.mcp.tools import WHATIF_TOOLS_SCHEMA, list_whatif_scenarios_tool, simulate_scenario_tool

EXISTING_TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "get_stock", "description": "Получить остатки товаров", "parameters": {"type": "object", "properties": {"warehouse": {"type": "string"}, "nomenclature": {"type": "string"}, "min_quantity": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_sales", "description": "Получить данные о продажах", "parameters": {"type": "object", "properties": {"date_from": {"type": "string"}, "date_to": {"type": "string"}, "manager": {"type": "string"}}, "required": ["date_from", "date_to"]}}},
    {"type": "function", "function": {"name": "get_sales_by_manager", "description": "Продажи по менеджерам", "parameters": {"type": "object", "properties": {"date_from": {"type": "string"}, "date_to": {"type": "string"}, "manager": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_receivables", "description": "Задолженность клиентов", "parameters": {"type": "object", "properties": {"min_amount": {"type": "number"}, "date_from": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_purchases", "description": "Закупки товаров/услуг у поставщиков", "parameters": {"type": "object", "properties": {"date_from": {"type": "string"}, "date_to": {"type": "string"}, "item": {"type": "string"}, "supplier": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "forecast_sales", "description": "Прогноз продаж товара на N дней (Prophet/Holt-Winters/Linear)", "parameters": {"type": "object", "properties": {"nomenclature": {"type": "string"}, "days": {"type": "integer"}, "method": {"type": "string", "enum": ["auto", "prophet", "holt_winters", "linear"]}}, "required": ["nomenclature"]}}},
    {"type": "function", "function": {"name": "forecast_stockout", "description": "Прогноз окончания товаров на складе", "parameters": {"type": "object", "properties": {"lead_time_days": {"type": "integer"}, "safety_stock_days": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "compare_forecasts", "description": "Сравнение методов прогнозирования (Linear/Holt-Winters/Prophet)", "parameters": {"type": "object", "properties": {"nomenclature": {"type": "string"}, "test_days": {"type": "integer"}}, "required": ["nomenclature"]}}},
    {"type": "function", "function": {"name": "abc_xyz_analysis", "description": "ABC/XYZ классификация товаров/клиентов по выручке и стабильности", "parameters": {"type": "object", "properties": {"date_from": {"type": "string"}, "date_to": {"type": "string"}, "group_by": {"type": "string", "enum": ["nomenclature", "client", "manager"]}}, "required": ["date_from", "date_to"]}}},
    {"type": "function", "function": {"name": "list_nomenclature", "description": "Поиск номенклатуры", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "create_chart", "description": "Построить график. Если данные позволяют drill-down (иерархия категорий/клиентов/территории/времени), укажите domain_id из: sales_by_category, sales_by_customer, sales_by_territory, time", "parameters": {"type": "object", "properties": {"chart_type": {"type": "string", "enum": ["line", "bar", "hbar", "pie", "area"]}, "title": {"type": "string"}, "x_data": {"type": "array"}, "y_data": {"type": "array"}, "x_label": {"type": "string"}, "y_label": {"type": "string"}, "series_names": {"type": "array"}, "color_scheme": {"type": "string", "enum": ["default", "corporate", "vibrant"]}, "domain_id": {"type": "string", "enum": ["sales_by_category", "sales_by_customer", "sales_by_territory", "time"], "description": "Домен для drill-down детализации"}}, "required": ["chart_type", "title", "x_data", "y_data"]}}},
    {"type": "function", "function": {"name": "drill_down", "description": "Детализация графика: получить данные следующего уровня иерархии по клику на элемент. Вызывается когда пользователь кликает на элемент графика с drilldown.enabled=true", "parameters": {"type": "object", "properties": {"domain": {"type": "string", "enum": ["sales_by_category", "sales_by_customer", "sales_by_territory", "time"], "description": "Домен из исходного графика"}, "parent_level": {"type": "string", "description": "Текущий уровень (например category)"}, "parent_value": {"type": "string", "description": "Значение, на которое кликнули"}, "child_level": {"type": "string", "description": "Целевой уровень детализации (например subcategory)"}, "date_from": {"type": "string", "description": "Начало периода YYYY-MM-DD"}, "date_to": {"type": "string", "description": "Конец периода YYYY-MM-DD"}, "metric": {"type": "string", "enum": ["revenue", "quantity"], "description": "Метрика агрегации"}}, "required": ["domain", "parent_level", "parent_value", "child_level"]}}},
    {"type": "function", "function": {"name": "get_analytics_context", "description": "Получить полный контекст для аналитики одним batch-запросом (итоги, топ-20 товаров, топ-10 клиентов, остатки, неликвиды)", "parameters": {"type": "object", "properties": {"date_from": {"type": "string", "description": "Начальная дата (YYYY-MM-DD)"}, "date_to": {"type": "string", "description": "Конечная дата (YYYY-MM-DD)"}}, "required": ["date_from", "date_to"]}}},
    {"type": "function", "function": {"name": "get_sales_documents", "description": "Получить список документов реализации с номерами, датами, суммами и контрагентами. Используйте для проверки конкретных сделок, поиска по контрагенту, детализации продаж.", "parameters": {"type": "object", "properties": {"date_from": {"type": "string", "description": "Дата начала периода (YYYY-MM-DD)"}, "date_to": {"type": "string", "description": "Дата окончания периода (YYYY-MM-DD)"}, "counterparty": {"type": "string", "description": "Фильтр по контрагенту (подстрока)"}, "sum_min": {"type": "number", "description": "Минимальная сумма"}, "sum_max": {"type": "number", "description": "Максимальная сумма"}, "posted_only": {"type": "boolean", "description": "Только проведённые"}, "sort_by": {"type": "string", "enum": ["date", "sum", "number"], "description": "Поле сортировки"}, "sort_order": {"type": "string", "enum": ["asc", "desc"], "description": "Направление"}, "page": {"type": "integer", "description": "Номер страницы"}, "page_size": {"type": "integer", "description": "Размер страницы"}}, "required": ["date_from", "date_to"]}}},
    {"type": "function", "function": {"name": "get_executive_kpi", "description": "Агрегированные KPI для панели руководителя: выручка, прибыль, заказы, маржа, топ-менеджер, спарклайны. Сравнение с предыдущим периодом.", "parameters": {"type": "object", "properties": {"period": {"type": "string", "enum": ["today", "yesterday", "this_week", "last_week", "this_month", "last_month", "this_quarter", "this_year"], "description": "Период расчёта"}, "organization": {"type": "string", "description": "Фильтр по организации (наименование или GUID)"}, "include_sparklines": {"type": "boolean", "description": "Включать данные для мини-графиков"}}, "required": []}}},
    {"type": "function", "function": {"name": "generate_executive_summary", "description": "AI-сводка для руководителя: анализ KPI с выделением аномалий и рекомендациями через DeepSeek.", "parameters": {"type": "object", "properties": {"period": {"type": "string", "enum": ["today", "yesterday", "this_week", "last_week", "this_month", "last_month", "this_quarter", "this_year"], "description": "Период"}, "organization": {"type": "string", "description": "Фильтр по организации"}, "include_sparklines": {"type": "boolean"}}, "required": []}}},
    {"type": "function", "function": {"name": "config", "description": "Получить паспорт базы 1С: имя, конфигурация, версия, платформа.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "describe", "description": "Описать объекты метаданных в базе 1С (справочники, документы, регистры).", "parameters": {"type": "object", "properties": {"object_type": {"type": "string", "description": "Тип объекта: Catalog, Document, AccumulationRegister, InformationRegister"}, "search": {"type": "string", "description": "Поиск по имени"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_structure", "description": "Получить структуру объекта метаданных: поля, типы, синонимы.", "parameters": {"type": "object", "properties": {"object_name": {"type": "string", "description": "Имя объекта (например, Номенклатура, Продажи)"}}, "required": ["object_name"]}}},
]

ALL_TOOLS_SCHEMA = EXISTING_TOOLS_SCHEMA + WHATIF_TOOLS_SCHEMA

TOOLS_REGISTRY: dict[str, Any] = {
    "get_stock": get_stock_tool,
    "get_sales": get_sales_tool,
    "get_sales_by_manager": get_sales_by_manager_tool,
    "get_receivables": get_receivables_tool,
    "abc_xyz_analysis": abc_xyz_analysis_tool,
    "forecast_sales": forecast_sales_tool,
    "forecast_stockout": forecast_stockout_tool,
    "compare_forecasts": compare_forecasts_tool,
    "list_nomenclature": list_nomenclature_tool,
    "get_purchases": get_purchases_tool,
    "create_chart": create_chart_tool,
    "drill_down": drill_down_tool,
    "simulate_scenario": simulate_scenario_tool,
    "list_whatif_scenarios": list_whatif_scenarios_tool,
    "get_analytics_context": get_analytics_context_tool,
    "get_sales_documents": get_sales_documents_tool,
    "get_executive_kpi": get_executive_kpi_tool,
    "generate_executive_summary": generate_executive_summary_tool,
    "config": config_tool,
    "describe": describe_tool,
    "get_structure": get_structure_tool,
}


def get_tool_function(tool_name: str) -> Any:
    if tool_name not in TOOLS_REGISTRY:
        raise ValueError(f"Неизвестный tool: {tool_name}. Доступны: {list(TOOLS_REGISTRY.keys())}")
    return TOOLS_REGISTRY[tool_name]


def list_all_tools() -> list[str]:
    return list(TOOLS_REGISTRY.keys())
