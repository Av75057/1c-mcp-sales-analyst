from __future__ import annotations

from typing import Any

from src.analysis.abc_xyz import analyze as abc_xyz_analyze
from src.logger import logger


async def abc_xyz_analysis_tool(
    date_from: str = "",
    date_to: str = "",
    group_by: str = "nomenclature",
    abc_thresholds: list[int] | None = None,
    xyz_thresholds: list[int] | None = None,
) -> dict[str, Any]:
    logger.info("ABC/XYZ: период {}-{}, group_by={}", date_from, date_to, group_by)

    from src.tools import get_client
    client = get_client()
    sales = await client.get_sales(date_from=date_from or None, date_to=date_to or None)
    if not sales:
        return {"error": "Нет данных о продажах за указанный период"}

    result = abc_xyz_analyze(sales, date_from=date_from, date_to=date_to, group_by=group_by, abc_thresholds=abc_thresholds, xyz_thresholds=xyz_thresholds)

    return {
        "summary": result.summary,
        "matrix": result.matrix,
        "recommendations": result.recommendations,
        "categories": {k: v[:5] for k, v in result.categories.items()},
    }


ABC_XYZ_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "abc_xyz_analysis",
        "description": "ABC/XYZ классификация товаров/клиентов по выручке и стабильности спроса",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Начальная дата (YYYY-MM-DD)"},
                "date_to": {"type": "string", "description": "Конечная дата (YYYY-MM-DD)"},
                "group_by": {"type": "string", "enum": ["nomenclature", "client", "manager"], "description": "Группировка"},
                "abc_thresholds": {"type": "array", "items": {"type": "integer"}, "description": "Границы ABC (по умолчанию [80, 95])"},
                "xyz_thresholds": {"type": "array", "items": {"type": "integer"}, "description": "Границы XYZ (по умолчанию [10, 25])"},
            },
            "required": ["date_from", "date_to"],
        },
    },
}
