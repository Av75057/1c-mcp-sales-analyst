from __future__ import annotations

from datetime import date, datetime
from typing import Any


def validate_document(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    items = data.get("items", [])
    totals = data.get("totals", {})
    header = data.get("header", {})

    calc_subtotal = sum(i.get("sum_without_vat", i.get("sum", 0)) for i in items)
    calc_vat = sum(i.get("vat_sum", 0) for i in items)
    calc_total = sum(i.get("sum_with_vat", i.get("sum_without_vat", i.get("sum", 0))) for i in items)

    if totals.get("subtotal") and abs(totals["subtotal"] - calc_subtotal) > 1:
        warnings.append({"field": "totals.subtotal", "message": f"Сумма по строкам ({calc_subtotal:.2f}) отличается от итога ({totals['subtotal']:.2f})"})

    if totals.get("total") and abs(totals["total"] - calc_total) > 1:
        errors.append({"field": "totals.total", "message": f"Итого по строкам ({calc_total:.2f}) не сходится с документом ({totals['total']:.2f})"})

    for i, item in enumerate(items):
        name = item.get("name", "")
        qty = item.get("quantity", 0)
        price = item.get("price", 0)
        raw_sum = item.get("sum_without_vat", item.get("sum", 0))
        if qty > 0 and price > 0 and raw_sum > 0:
            expected = round(qty * price, 2)
            if abs(expected - raw_sum) > 1:
                warnings.append({"field": f"items[{i}].sum", "message": f"Сумма строки '{name}': {expected:.2f} ≠ {raw_sum:.2f}"})

        vat_rate = item.get("vat_rate", 0)
        vat_sum = item.get("vat_sum", 0)
        if vat_rate > 0 and raw_sum > 0 and vat_sum > 0:
            expected_vat = round(raw_sum * vat_rate / 100, 2)
            if abs(expected_vat - vat_sum) > 1:
                warnings.append({"field": f"items[{i}].vat", "message": f"НДС строки '{name}': {expected_vat:.2f} ≠ {vat_sum:.2f}"})

    date_str = header.get("date", "")
    if date_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            if d > date.today():
                warnings.append({"field": "header.date", "message": f"Дата в будущем: {date_str}"})
            if d < date(2020, 1, 1):
                warnings.append({"field": "header.date", "message": f"Дата больше 5 лет назад: {date_str}"})
        except ValueError:
            errors.append({"field": "header.date", "message": f"Некорректный формат даты: {date_str}"})

    inn = header.get("inn", "")
    if inn:
        inn_clean = inn.replace(" ", "").replace("-", "")
        if not (len(inn_clean) in (10, 12) and inn_clean.isdigit()):
            warnings.append({"field": "header.inn", "message": f"Некорректный ИНН: {inn}"})

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "calculated": {"subtotal": calc_subtotal, "vat_total": calc_vat, "total": calc_total},
        "totals_match": abs(calc_total - totals.get("total", 0)) <= 1 if totals.get("total") else True,
    }
