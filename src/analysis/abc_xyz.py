from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.logger import logger


@dataclass
class ABCXYZResult:
    summary: dict[str, Any] = field(default_factory=dict)
    matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    categories: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    items_df: pd.DataFrame = field(default_factory=pd.DataFrame)


STRATEGIES = {
    "AX": "Всегда в наличии, автопополнение, страховой запас 15 дней",
    "AY": "Страховой запас 30 дней, еженедельный мониторинг",
    "AZ": "Работа под заказ, минимальный складской запас",
    "BX": "Оптимальный запас (EOQ), ежемесячная проверка",
    "BY": "Периодический контроль, запас на 30-45 дней",
    "BZ": "Под заказ или минимальный запас, снижение закупок",
    "CX": "Низкий приоритет, заказ партиями",
    "CY": "Кандидаты на сокращение, разовые партии",
    "CZ": "Вывод из ассортимента, распродажа остатков",
}


def analyze(
    sales_data: list[dict[str, Any]],
    date_from: str = "",
    date_to: str = "",
    group_by: str = "nomenclature",
    abc_thresholds: list[int] | None = None,
    xyz_thresholds: list[int] | None = None,
) -> ABCXYZResult:
    logger.info("ABC/XYZ анализ: {} записей, период {} - {}", len(sales_data), date_from, date_to)

    abc_t = abc_thresholds or [80, 95]
    xyz_t = xyz_thresholds or [10, 25]

    df = pd.DataFrame(sales_data)
    if df.empty:
        return ABCXYZResult(summary={"total_items": 0, "total_revenue": 0, "error": "Нет данных"})

    name_col = {"nomenclature": "nomenclature", "client": "client", "manager": "manager"}.get(group_by, "nomenclature")
    if name_col not in df.columns:
        name_col = "nomenclature"
    if name_col not in df.columns:
        df[name_col] = "Unknown"

    revenue_col = "sum"
    qty_col = "quantity"

    if revenue_col not in df.columns:
        revenue_col = "sum_with_vat"
    if revenue_col not in df.columns:
        revenue_col = "sum_without_vat"

    revenue = df.groupby(name_col)[revenue_col].sum().sort_values(ascending=False).reset_index()
    revenue.columns = ["item", "revenue"]
    total_rev = revenue["revenue"].sum()
    revenue["share"] = revenue["revenue"] / total_rev * 100
    revenue["cumulative"] = revenue["share"].cumsum()

    revenue["abc_class"] = "C"
    if abc_t[0] > 0:
        revenue.loc[revenue["cumulative"] <= abc_t[0], "abc_class"] = "A"
        revenue.loc[(revenue["cumulative"] > abc_t[0]) & (revenue["cumulative"] <= abc_t[1]), "abc_class"] = "B"

    if date_from and date_to:
        from datetime import datetime
        try:
            df["date"] = pd.to_datetime(df["date"])
            df["month"] = df["date"].dt.to_period("M").astype(str)
        except Exception:
            df["month"] = "all"

        xyz_data = []
        for item in revenue["item"].unique():
            item_sales = df[df[name_col] == item]
            monthly = item_sales.groupby("month")[qty_col].sum() if "month" in item_sales.columns else item_sales[qty_col]
            mu = monthly.mean()
            sigma = monthly.std()
            cv = (sigma / mu * 100) if mu > 0 else 999
            xyz_class = "X" if cv <= xyz_t[0] else "Y" if cv <= xyz_t[1] else "Z"
            xyz_data.append({"item": item, "cv": round(cv, 1), "xyz_class": xyz_class})

        xyz_df = pd.DataFrame(xyz_data)
        revenue = revenue.merge(xyz_df, on="item", how="left")
        revenue["xyz_class"] = revenue.get("xyz_class", "Z").fillna("Z")
        revenue["cv"] = revenue.get("cv", 999).fillna(999)
    else:
        revenue["xyz_class"] = "X"
        revenue["cv"] = 0

    revenue["category"] = revenue["abc_class"] + revenue["xyz_class"]

    matrix: dict[str, dict[str, float]] = {}
    for cat in ["AX", "AY", "AZ", "BX", "BY", "BZ", "CX", "CY", "CZ"]:
        subset = revenue[revenue["category"] == cat]
        cat_rev = subset["revenue"].sum()
        matrix[cat] = {"count": int(len(subset)), "revenue": round(cat_rev, 2), "share": round(cat_rev / total_rev * 100, 1) if total_rev > 0 else 0}

    categories: dict[str, list[dict[str, Any]]] = {}
    for cat in ["AX", "AY", "AZ", "BX", "BY", "BZ", "CX", "CY", "CZ"]:
        subset = revenue[revenue["category"] == cat].head(10)
        categories[cat] = [
            {"item": r["item"], "revenue": round(r["revenue"], 2), "abc_class": r["abc_class"], "xyz_class": r["xyz_class"], "cv": r["cv"], "cumulative_share": round(r["cumulative"], 1), "recommendation": STRATEGIES.get(cat, "")}
            for _, r in subset.iterrows()
        ]

    recommendations = []
    for cat in ["CZ", "CY", "AZ", "BZ"]:
        if matrix[cat]["count"] > 0:
            savings = round(matrix[cat]["revenue"] * 0.1, 2)
            recommendations.append({"category": cat, "action": STRATEGIES.get(cat, ""), "items_count": matrix[cat]["count"], "potential_savings": savings, "description": f"{matrix[cat]['count']} товаров ({matrix[cat]['share']:.1f}% выручки)"})

    summary = {"period_from": date_from, "period_to": date_to, "total_items": int(len(revenue)), "total_revenue": round(total_rev, 2), "analysis_type": group_by}

    return ABCXYZResult(summary=summary, matrix=matrix, categories=categories, recommendations=recommendations, items_df=revenue)
