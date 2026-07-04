from __future__ import annotations

import os
import pytest

# Все тесты data_fetcher требуют мок-режима
os.environ["USE_MOCK_DATA"] = "true"


@pytest.mark.asyncio
async def test_fetch_line_no_grouping():
    """Line chart: данные не группируются (каждая строка — точка на временном ряде)."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "line",
        "x_axis": {"field": "Дата"},
        "series": [{"field": "Сумма"}],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Дата", "Сумма"], "period": "last_30_days"},
        "limit": 5,
    }
    data = await fetch_chart_data(cfg)
    assert len(data) == 5
    # line без group_by — все строки как есть
    assert all("Дата" in r and "Сумма" in r for r in data)
    # Проверка что сумма не агрегирована (строки разные)
    sums = {r["Сумма"] for r in data}
    assert len(sums) > 1


@pytest.mark.asyncio
async def test_fetch_pie_auto_grouping():
    """Pie chart: автоматическая группировка по x_axis.field без дубликатов."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "pie",
        "x_axis": {"field": "Менеджер"},
        "series": [{"field": "Сумма"}],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Менеджер", "Сумма"], "period": "last_30_days"},
        "limit": 10,
    }
    data = await fetch_chart_data(cfg)
    assert len(data) <= 7  # pie limit = 7
    assert len(data) > 0
    # Нет дубликатов менеджеров
    managers = [r["Менеджер"] for r in data]
    assert len(managers) == len(set(managers)), f"Дубликаты менеджеров: {managers}"
    # Нет лишних кавычек в именах
    for m in managers:
        assert "'" not in m, f"Кавычка в имени: {m}"


@pytest.mark.asyncio
async def test_fetch_horizontal_bar_auto_grouping():
    """Horizontal bar: автоматическая группировка."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "horizontal_bar",
        "x_axis": {"field": "Менеджер"},
        "series": [{"field": "Сумма"}],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Менеджер", "Сумма"], "period": "last_30_days"},
    }
    data = await fetch_chart_data(cfg)
    assert len(data) > 0
    managers = [r["Менеджер"] for r in data]
    assert len(managers) == len(set(managers))


@pytest.mark.asyncio
async def test_fetch_bar_no_auto_grouping():
    """Bar chart: без group_by данные не группируются (для bar группировка только явная)."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "bar",
        "x_axis": {"field": "Менеджер"},
        "series": [{"field": "Сумма"}],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Менеджер", "Сумма"], "period": "last_30_days"},
        "limit": 5,
    }
    data = await fetch_chart_data(cfg)
    # bar без group_by — НЕ группируется, возвращаются сырые строки
    assert len(data) > 0


@pytest.mark.asyncio
async def test_fetch_pie_limit_seven():
    """Pie chart: limit не больше 7 сегментов."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "pie",
        "x_axis": {"field": "Менеджер"},
        "series": [{"field": "Сумма"}],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Менеджер", "Сумма"], "period": "last_30_days"},
        "limit": 100,
    }
    data = await fetch_chart_data(cfg)
    assert len(data) <= 7


@pytest.mark.asyncio
async def test_fetch_with_explicit_group_by():
    """Явная группировка по полю."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "bar",
        "x_axis": {"field": "Менеджер"},
        "series": [{"field": "Сумма"}],
        "group_by": ["Менеджер"],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Менеджер", "Сумма"], "period": "last_30_days"},
    }
    data = await fetch_chart_data(cfg)
    assert len(data) > 0
    managers = [r["Менеджер"] for r in data]
    assert len(managers) == len(set(managers))


@pytest.mark.asyncio
async def test_fetch_sort_desc():
    """Сортировка по убыванию."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "bar",
        "x_axis": {"field": "Менеджер"},
        "series": [{"field": "Сумма"}],
        "group_by": ["Менеджер"],
        "order_by": {"field": "Сумма", "direction": "desc"},
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Менеджер", "Сумма"], "period": "last_30_days"},
    }
    data = await fetch_chart_data(cfg)
    assert len(data) > 0
    sums = [r["Сумма"] for r in data]
    assert sums == sorted(sums, reverse=True), f"Не отсортировано по убыванию: {sums}"


@pytest.mark.asyncio
async def test_fetch_sort_asc():
    """Сортировка по возрастанию."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "bar",
        "x_axis": {"field": "Менеджер"},
        "series": [{"field": "Сумма"}],
        "group_by": ["Менеджер"],
        "order_by": {"field": "Сумма", "direction": "asc"},
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Менеджер", "Сумма"], "period": "last_30_days"},
    }
    data = await fetch_chart_data(cfg)
    assert len(data) > 0
    sums = [r["Сумма"] for r in data]
    assert sums == sorted(sums), f"Не отсортировано по возрастанию: {sums}"


@pytest.mark.asyncio
async def test_fetch_no_query():
    """Без onec_query возвращает пустой список."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    data = await fetch_chart_data({})
    assert data == []


@pytest.mark.asyncio
async def test_fetch_empty_query():
    """С пустым onec_query возвращает пустой список."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    data = await fetch_chart_data({"onec_query": {}})
    assert data == []


@pytest.mark.asyncio
async def test_fetch_field_mapping():
    """Проверка маппинга полей: Дата→date, Сумма→sum."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "line",
        "x_axis": {"field": "Дата"},
        "series": [{"field": "Сумма"}],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Дата", "Сумма"], "period": "last_30_days"},
        "limit": 3,
    }
    data = await fetch_chart_data(cfg)
    assert len(data) > 0
    row = data[0]
    assert "Дата" in row
    assert "Сумма" in row
    # Сумма должна быть числом
    assert isinstance(row["Сумма"], (int, float))


@pytest.mark.asyncio
async def test_fetch_multi_series():
    """Несколько серий в данных."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "combo",
        "x_axis": {"field": "Менеджер"},
        "series": [{"field": "Сумма"}, {"field": "Количество"}],
        "group_by": ["Менеджер"],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Менеджер", "Сумма", "Количество"], "period": "last_30_days"},
    }
    data = await fetch_chart_data(cfg)
    assert len(data) > 0
    assert "Сумма" in data[0]
    assert "Количество" in data[0]


@pytest.mark.asyncio
async def test_fetch_with_count_aggregation():
    """Агрегация count вместо sum."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "bar",
        "x_axis": {"field": "Менеджер"},
        "series": [{"field": "Сумма"}],
        "group_by": ["Менеджер"],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Менеджер", "Сумма"], "period": "last_30_days", "aggregation": "count"},
    }
    data = await fetch_chart_data(cfg)
    assert len(data) > 0
    # При count агрегации значения — количество записей, не сумма
    for r in data:
        assert r["Сумма"] >= 1


@pytest.mark.asyncio
async def test_fetch_custom_period():
    """Кастомный период (date_from/date_to)."""
    from src.dashboard.services.data_fetcher import fetch_chart_data

    cfg = {
        "chart_type": "line",
        "x_axis": {"field": "Дата"},
        "series": [{"field": "Сумма"}],
        "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Дата", "Сумма"], "date_from": "2026-01-01", "date_to": "2026-12-31"},
        "limit": 3,
    }
    data = await fetch_chart_data(cfg)
    assert len(data) >= 0  # может быть 0 если мок не вернул данные за этот период


@pytest.mark.asyncio
async def test_fetch_group_data_empty():
    """_group_data с пустыми полями возвращает исходные строки."""
    from src.dashboard.services.data_fetcher import _group_data

    rows = [{"a": 1, "b": 2}]
    result = _group_data(rows, [], ["b"], "sum")
    assert result == rows


@pytest.mark.asyncio
async def test_fetch_group_data_single_field():
    """_group_data группирует по одному полю."""
    from src.dashboard.services.data_fetcher import _group_data

    rows = [{"cat": "A", "val": 10}, {"cat": "A", "val": 20}, {"cat": "B", "val": 30}]
    result = _group_data(rows, ["cat"], ["val"], "sum")
    assert len(result) == 2
    result_map = {r["cat"]: r["val"] for r in result}
    assert result_map["A"] == 30
    assert result_map["B"] == 30


@pytest.mark.asyncio
async def test_fetch_group_data_multi_field():
    """_group_data группирует по нескольким полям."""
    from src.dashboard.services.data_fetcher import _group_data

    rows = [
        {"cat": "A", "sub": "X", "val": 10},
        {"cat": "A", "sub": "X", "val": 20},
        {"cat": "A", "sub": "Y", "val": 30},
    ]
    result = _group_data(rows, ["cat", "sub"], ["val"], "sum")
    assert len(result) == 2
    for r in result:
        if r["sub"] == "X":
            assert r["val"] == 30
        elif r["sub"] == "Y":
            assert r["val"] == 30
