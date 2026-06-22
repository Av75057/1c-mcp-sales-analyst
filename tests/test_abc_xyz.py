from __future__ import annotations

import pytest
import numpy as np

from src.analysis.abc_xyz import analyze, STRATEGIES


def _make_sales(items: list[str], revenues: list[float], dates: list[str] | None = None) -> list[dict]:
    data = []
    for i, name in enumerate(items):
        for _ in range(3):
            data.append({"nomenclature": name, "sum": revenues[i] / 3, "date": dates[i] if dates else "2026-01-01", "quantity": 10, "manager": "Test"})
    return data


def test_abc_classification_a():
    sales = _make_sales(["A1", "A2", "B1", "C1", "C2"], [4000, 3000, 1500, 1000, 500], ["2026-01-01"] * 5)
    r = analyze(sales)
    assert r.summary["total_items"] == 5
    assert r.summary["total_revenue"] == 10000


def test_abc_top_items_are_a():
    sales = _make_sales(["Товар1", "Товар2", "Товар3"], [800, 150, 50], ["2026-01-01"] * 3)
    r = analyze(sales)
    assert r.matrix["AX"]["count"] == 1
    assert r.matrix["BX"]["count"] == 1
    assert r.matrix["CX"]["count"] == 1


def test_empty_data():
    r = analyze([])
    assert r.summary["total_items"] == 0


def test_matrix_has_all_categories():
    sales = _make_sales(["X", "Y", "Z"], [100, 50, 30], ["2026-01-01"] * 3)
    r = analyze(sales)
    for cat in ["AX", "AY", "AZ", "BX", "BY", "BZ", "CX", "CY", "CZ"]:
        assert cat in r.matrix


def test_recommendations_exist():
    data = []
    for name, rev in [("A", 800), ("B", 150), ("C", 50), ("D", 100)]:
        for m in range(1, 7):
            np.random.seed(m)
            noise = np.random.uniform(0.5, 1.5)
            data.append({"nomenclature": name, "sum": rev / 6 * noise, "date": f"2026-{m:02d}-01", "quantity": int(10 * noise), "manager": "Test"})
    r = analyze(data, date_from="2026-01-01", date_to="2026-06-30")
    assert len(r.recommendations) > 0


def test_custom_thresholds():
    sales = _make_sales(["A", "B", "C"], [500, 300, 200], ["2026-01-01"] * 3)
    r = analyze(sales, abc_thresholds=[50, 90])
    assert r.matrix["AX"]["count"] == 1


def test_strategies_exist():
    assert "AX" in STRATEGIES
    assert "CZ" in STRATEGIES
    assert "BY" in STRATEGIES
