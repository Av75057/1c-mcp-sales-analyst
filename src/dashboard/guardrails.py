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
    if chart_type not in ("line", "bar", "pie"):
        raise GuardrailError(f"Недопустимый тип графика: {chart_type}")

    if chart_type == "pie":
        limit = config.get("limit", 10)
        if limit > 7:
            config["limit"] = 7
