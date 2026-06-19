from __future__ import annotations

import os

import pytest

from src.charts.tool import create_chart_tool


def test_create_chart_valid():
    r = create_chart_tool("line", "Test", ["A", "B"], [10, 20])
    assert "chart_id" in r
    assert "image_base64" in r


def test_create_chart_too_many_points():
    r = create_chart_tool("line", "Test", list(range(101)), list(range(101)))
    assert "error" in r


def test_create_chart_pie_too_many():
    r = create_chart_tool("pie", "Test", list("ABCDEFGHI"), list(range(9)))
    assert "error" in r


def test_create_chart_hbar_too_many():
    r = create_chart_tool("hbar", "Test", list(range(16)), list(range(16)))
    assert "error" in r


def test_create_chart_invalid_type():
    r = create_chart_tool("invalid_type", "Test", ["A"], [1])
    assert "error" in r


def test_create_chart_all_types():
    for ct in ("line", "bar", "hbar", "pie", "area"):
        r = create_chart_tool(ct, f"Test {ct}", ["A", "B", "C"], [10, 20, 15])
        assert "chart_id" in r, f"Failed for {ct}"


def test_create_chart_multi_series():
    r = create_chart_tool("bar", "Multi", ["A", "B"], [[10, 20], [15, 25]], series_names=["X", "Y"])
    assert "chart_id" in r
