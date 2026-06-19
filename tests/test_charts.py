from __future__ import annotations

import base64
import os

import pytest

from src.charts.engine import render_chart


def test_line_chart():
    r = render_chart("line", "Test", ["A", "B", "C"], [10, 20, 15], "X", "Y")
    assert r["chart_id"].startswith("chart_")
    assert len(r["html"]) > 100
    assert "image_base64" in r
    assert os.path.exists(r["image_path"])


def test_bar_chart():
    r = render_chart("bar", "Test", ["A", "B"], [10, 20])
    assert r["metadata"]["chart_type"] == "bar"


def test_bar_multi_series():
    r = render_chart("bar", "Multi", ["A", "B"], [[10, 20], [15, 25]], series_names=["X", "Y"])
    assert r["metadata"]["chart_type"] == "bar"


def test_hbar_chart():
    r = render_chart("hbar", "Top Items", ["Long Item Name Here", "Short"], [100, 50])
    assert r["metadata"]["data_points"] == 2


def test_pie_chart():
    r = render_chart("pie", "Distribution", ["A", "B", "C"], [50, 30, 20])
    assert r["metadata"]["chart_type"] == "pie"


def test_area_chart():
    r = render_chart("area", "Cumulative", ["Jan", "Feb", "Mar"], [10, 25, 45])
    assert r["metadata"]["chart_type"] == "area"


def test_line_multi_series():
    r = render_chart("line", "Multi Line", ["A", "B"], [[10, 20], [15, 25]], series_names=["S1", "S2"])
    assert r["metadata"]["chart_type"] == "line"
    assert r["metadata"]["data_points"] == 2


def test_image_content():
    r = render_chart("line", "Img Test", ["X", "Y"], [1, 2])
    img_bytes = base64.b64decode(r["image_base64"])
    assert len(img_bytes) > 1000


def test_color_schemes():
    for scheme in ("default", "corporate", "vibrant"):
        r = render_chart("line", f"Scheme {scheme}", ["A", "B"], [1, 2], color_scheme=scheme)
        assert "image_base64" in r


def test_html_output():
    r = render_chart("line", "HTML Test", ["A", "B"], [1, 2], format="both")
    assert '<div' in r["html"]
    assert "Plotly" in r["html"] or "plotly" in r["html"]
