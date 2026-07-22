from __future__ import annotations

from typing import Any

from src.charts.engine import render_chart
from src.logger import logger

DRILLDOWN_DOMAINS: dict[str, dict[str, Any]] = {
    "sales_by_category": {
        "label": "Продажи по категориям",
        "levels": [
            {"id": "category", "label": "Категория", "has_children": True},
            {"id": "subcategory", "label": "Подкатегория", "has_children": True},
            {"id": "sku", "label": "SKU", "has_children": True},
            {"id": "document", "label": "Документы", "has_children": False},
        ],
    },
    "sales_by_customer": {
        "label": "Продажи по клиентам",
        "levels": [
            {"id": "segment", "label": "Сегмент", "has_children": True},
            {"id": "customer", "label": "Контрагент", "has_children": True},
            {"id": "contract", "label": "Договор", "has_children": True},
            {"id": "document", "label": "Документы", "has_children": False},
        ],
    },
    "sales_by_territory": {
        "label": "Продажи по территории",
        "levels": [
            {"id": "region", "label": "Регион", "has_children": True},
            {"id": "city", "label": "Город", "has_children": True},
            {"id": "store", "label": "Магазин/Склад", "has_children": True},
            {"id": "manager", "label": "Менеджер", "has_children": True},
            {"id": "sku", "label": "SKU", "has_children": False},
        ],
    },
    "time": {
        "label": "Временной",
        "levels": [
            {"id": "year", "label": "Год", "has_children": True},
            {"id": "quarter", "label": "Квартал", "has_children": True},
            {"id": "month", "label": "Месяц", "has_children": True},
            {"id": "week", "label": "Неделя", "has_children": True},
            {"id": "day", "label": "День", "has_children": False},
        ],
    },
}


def create_chart_tool(
    chart_type: str,
    title: str,
    x_data: list[Any],
    y_data: list[Any],
    x_label: str = "",
    y_label: str = "",
    series_names: list[str] | None = None,
    color_scheme: str = "default",
    domain_id: str = "",
) -> dict[str, Any]:
    logger.info("create_chart: type={}, title={}, points={}", chart_type, title, len(x_data))

    if len(x_data) > 100:
        return {
            "error": f"Слишком много точек данных ({len(x_data)}). Максимум 100. Пожалуйста, агрегируйте данные.",
        }

    if chart_type == "pie" and len(x_data) > 8:
        return {
            "error": f"Для круговой диаграммы слишком много категорий ({len(x_data)}). Максимум 8. Объедините мелкие категории в 'Прочее'.",
        }

    if chart_type == "hbar" and len(x_data) > 15:
        return {
            "error": f"Для горизонтального бара слишком много элементов ({len(x_data)}). Максимум 15. Возьмите топ-15.",
        }

    if chart_type not in ("line", "bar", "hbar", "pie", "area"):
        return {"error": f"Неизвестный тип графика: {chart_type}. Допустимые: line, bar, hbar, pie, area"}

    table_data = [
        {"label": str(x), "value": float(y) if y is not None else 0}
        for x, y in zip(x_data, y_data)
    ]
    result = {
        "table_data": table_data,
        "chart_type": chart_type,
        "title": title,
        "x_label": x_label,
        "y_label": y_label,
        "chart_id": "",
    }
    # Auto-detect domain if not provided
    if not domain_id:
        title_lower = (title + " " + x_label).lower()
        if any(w in title_lower for w in ["категори", "товар", "номенклатур", "продаж"]):
            domain_id = "sales_by_category"
        elif any(w in title_lower for w in ["клиент", "контрагент", "покупател"]):
            domain_id = "sales_by_customer"
        elif any(w in title_lower for w in ["регион", "город", "склад", "магазин", "территори"]):
            domain_id = "sales_by_territory"
        elif any(w in title_lower for w in ["год", "квартал", "месяц", "недел"]):
            domain_id = "time"
    # Attach drilldown context if domain is recognized
    domain = DRILLDOWN_DOMAINS.get(domain_id)
    if domain:
        result["domain_id"] = domain_id
        result["drilldown"] = {
            "enabled": True,
            "domain": domain_id,
            "domain_label": domain["label"],
            "current_level": domain["levels"][0]["id"],
            "levels": domain["levels"],
        }
    try:
        img = render_chart(
            chart_type=chart_type,
            title=title,
            x_data=x_data,
            y_data=y_data,
            x_label=x_label,
            y_label=y_label,
            series_names=series_names,
            color_scheme=color_scheme,
            format="png",
        )
        if isinstance(img, dict) and "image_base64" in img:
            result["image_base64"] = img["image_base64"]
        if isinstance(img, dict) and "metadata" in img:
            result["metadata"] = img["metadata"]
    except Exception as e:
        logger.warning("Chart image export failed (interactive data available): {}", e)
    return result
