from __future__ import annotations

from typing import Any

from src.charts.engine import render_chart
from src.logger import logger


def create_chart_tool(
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

    try:
        result = render_chart(
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
        return result
    except Exception as e:
        logger.error("Ошибка создания графика: {}", e)
        return {"error": f"Ошибка при создании графика: {e}"}
