from __future__ import annotations

from typing import Any

ALLOWED_FIELDS: dict[str, list[str]] = {
    "Document.РеализацияТоваровУслуг": ["Дата", "Контрагент", "Номенклатура", "Сумма", "Количество", "Менеджер", "Организация", "Номенклатура.Группа"],
    "Document.ЗаказКлиента": ["Дата", "Контрагент", "Сумма", "Статус", "Менеджер"],
    "Document.ПоступлениеНаРасчетныйСчет": ["Дата", "Контрагент", "Сумма", "СтатьяДвиженияДенежныхСредств"],
    "Catalog.Номенклатура": ["Наименование", "Артикул", "Группа", "Цена"],
    "Catalog.Контрагенты": ["Наименование", "Группа", "Менеджер"],
    "Register.Продажи": ["Период", "Номенклатура", "Контрагент", "Сумма", "Количество"],
}


class GuardrailError(ValueError):
    pass


VALID_CHART_TYPES = {"line", "bar", "pie", "horizontal_bar", "area", "combo", "scatter", "heatmap", "treemap", "sankey", "gauge", "radar"}
VALID_OPERATORS = {"eq", "ne", "gt", "lt", "gte", "lte", "between", "in", "contains"}


def validate_chart_config(config: dict[str, Any]) -> None:
    entity = config.get("onec_query", {}).get("entity", "")
    if entity not in ALLOWED_FIELDS:
        raise GuardrailError(f"Неизвестная сущность: {entity}")

    fields = config.get("onec_query", {}).get("fields", [])
    allowed = ALLOWED_FIELDS[entity]
    invalid = [f for f in fields if f not in allowed]
    if invalid:
        raise GuardrailError(f"Недопустимые поля: {invalid}. Разрешены: {allowed}")

    if config.get("drill_down", {}).get("enabled"):
        drill_entity = config["drill_down"].get("target_entity", "")
        if drill_entity not in ALLOWED_FIELDS:
            raise GuardrailError(f"Недопустимая сущность для drill-down: {drill_entity}")

    chart_type = config.get("chart_type", "")
    if chart_type not in VALID_CHART_TYPES:
        raise GuardrailError(f"Недопустимый тип графика: {chart_type}. Допустимы: {sorted(VALID_CHART_TYPES)}")

    if chart_type == "pie":
        limit = config.get("limit", 10)
        if limit > 7:
            config["limit"] = 7

    if chart_type == "combo":
        series = config.get("series", [])
        if len(series) < 2:
            raise GuardrailError("Combo-график требует минимум 2 серии")
        types = {s.get("type", "bar") for s in series}
        if len(types) < 2:
            raise GuardrailError("Combo-график требует серии разных типов (bar + line)")

    if chart_type == "scatter":
        x_type = config.get("x_axis", {}).get("type", "")
        if x_type != "value":
            raise GuardrailError("Scatter требует x_axis.type = 'value'")

    if chart_type == "heatmap":
        if not config.get("heatmap"):
            raise GuardrailError("Heatmap требует секцию 'heatmap' с x_field, y_field, value_field")

    if chart_type == "treemap":
        if not config.get("treemap"):
            raise GuardrailError("Treemap требует секцию 'treemap' с category_field, value_field")

    if chart_type == "sankey":
        if not config.get("sankey"):
            raise GuardrailError("Sankey требует секцию 'sankey' с source_field, target_field, value_field")

    if chart_type == "gauge":
        if not config.get("gauge"):
            raise GuardrailError("Gauge требует секцию 'gauge' с value_field")

    if chart_type == "radar":
        radar = config.get("radar", {})
        if not radar or len(radar.get("dimensions", [])) < 3:
            raise GuardrailError("Radar требует минимум 3 измерения в секции 'radar.dimensions'")

    for f in config.get("filters", []):
        op = f.get("operator", "")
        if op not in VALID_OPERATORS:
            raise GuardrailError(f"Недопустимый оператор фильтра: {op}. Допустимы: {sorted(VALID_OPERATORS)}")
        if op in ("gt", "lt", "gte", "lte") and not isinstance(f.get("value"), (int, float)):
            raise GuardrailError(f"Оператор {op} требует числовое значение")
        val_str = str(f.get("value", ""))
        if any(p in val_str for p in [";", "--", "/*", "exec("]):
            raise GuardrailError(f"Потенциальная инъекция в фильтре: {f}")
        if len(val_str) > 500:
            raise GuardrailError(f"Слишком длинное значение фильтра: {len(val_str)}")
