from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import plotly.io as pio

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "charts"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

COLOR_SCHEMES: dict[str, dict[str, Any]] = {
    "default": {
        "colors": ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"],
        "bg": "#ffffff",
        "paper_bg": "#ffffff",
        "font_color": "#333333",
        "grid_color": "#e8e8e8",
    },
    "corporate": {
        "colors": ["#1a56db", "#7c3aed", "#059669", "#d97706", "#dc2626", "#0891b2", "#4f46e5", "#65a30d"],
        "bg": "#ffffff",
        "paper_bg": "#f8fafc",
        "font_color": "#1e293b",
        "grid_color": "#e2e8f0",
    },
    "vibrant": {
        "colors": ["#FF006E", "#8338EC", "#3A86FF", "#FB5607", "#00BBF9", "#00F5D4", "#9B5DE5", "#F15BB5"],
        "bg": "#ffffff",
        "paper_bg": "#ffffff",
        "font_color": "#1a1a2e",
        "grid_color": "#e0e0e0",
    },
}


def _make_layout(title: str, x_label: str, y_label: str, scheme: str, width: int, height: int) -> dict[str, Any]:
    s = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES["default"])
    return {
        "title": {"text": title, "x": 0.5, "xanchor": "center", "font": {"size": 16, "color": s["font_color"]}},
        "xaxis": {"title": {"text": x_label}, "gridcolor": s["grid_color"], "zerolinecolor": s["grid_color"]},
        "yaxis": {"title": {"text": y_label}, "gridcolor": s["grid_color"], "zerolinecolor": s["grid_color"]},
        "plot_bgcolor": s["bg"],
        "paper_bgcolor": s["paper_bg"],
        "font": {"color": s["font_color"]},
        "margin": {"l": 60, "r": 30, "t": 50, "b": 60},
        "width": width,
        "height": height,
        "hovermode": "x unified",
        "legend": {"orientation": "h", "y": -0.2},
    }


def _truncate_labels(labels: list[str], max_len: int = 25) -> list[str]:
    return [l if len(l) <= max_len else l[: max_len - 1] + "…" for l in labels]


def render_chart(
    chart_type: str,
    title: str,
    x_data: list[Any],
    y_data: list[Any] | list[list[Any]],
    x_label: str = "",
    y_label: str = "",
    series_names: list[str] | None = None,
    width: int = 800,
    height: int = 500,
    color_scheme: str = "default",
    format: str = "png",
) -> dict[str, Any]:
    scheme = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    colors = scheme["colors"]
    layout = _make_layout(title, x_label, y_label, color_scheme, width, height)
    is_multi = y_data and isinstance(y_data[0], (list, tuple))

    fig = go.Figure()

    if chart_type == "line":
        if is_multi:
            for i, series in enumerate(y_data):
                fig.add_trace(go.Scatter(x=x_data, y=series, mode="lines+markers", name=series_names[i] if series_names else f"Серия {i+1}", line=dict(color=colors[i % len(colors)])))
        else:
            fig.add_trace(go.Scatter(x=x_data, y=y_data, mode="lines+markers", line=dict(color=colors[0])))
        layout["yaxis"].update({"rangemode": "tozero"})

    elif chart_type == "bar":
        if is_multi:
            for i, series in enumerate(y_data):
                fig.add_trace(go.Bar(x=x_data, y=series, name=series_names[i] if series_names else f"Серия {i+1}", marker=dict(color=colors[i % len(colors)])))
            layout["barmode"] = "group"
        else:
            fig.add_trace(go.Bar(x=x_data, y=y_data, marker=dict(color=colors[0])))
        layout["yaxis"].update({"rangemode": "tozero"})

    elif chart_type == "hbar":
        labels = _truncate_labels(list(reversed(x_data)) if x_data else [])
        values = list(reversed(y_data)) if not is_multi else y_data
        fig.add_trace(go.Bar(x=values, y=labels, orientation="h", marker=dict(color=colors[0])))
        layout["xaxis"].update({"rangemode": "tozero"})
        layout["yaxis"]["autorange"] = "reversed"

    elif chart_type == "pie":
        labels = _truncate_labels(list(x_data))
        fig.add_trace(go.Pie(labels=labels, values=y_data, hole=0.4, marker=dict(colors=colors), textinfo="label+percent", textposition="outside"))
        layout["legend"]["y"] = -0.3

    elif chart_type == "area":
        if is_multi:
            for i, series in enumerate(y_data):
                fig.add_trace(go.Scatter(x=x_data, y=series, mode="lines", fill="tozeroy", name=series_names[i] if series_names else f"Серия {i+1}", line=dict(color=colors[i % len(colors)])))
        else:
            fig.add_trace(go.Scatter(x=x_data, y=y_data, mode="lines", fill="tozeroy", line=dict(color=colors[0])))
        layout["yaxis"].update({"rangemode": "tozero"})

    fig.update_layout(**layout)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw = json.dumps({"x": x_data, "y": y_data, "type": chart_type}, sort_keys=True, ensure_ascii=False)
    chart_id = f"chart_{ts}_{hashlib.md5(raw.encode()).hexdigest()[:8]}"
    png_path = STATIC_DIR / f"{chart_id}.png"
    html_str = pio.to_html(fig, include_plotlyjs="cdn", full_html=False)

    result: dict[str, Any] = {
        "chart_id": chart_id,
        "html": html_str,
        "image_url": f"/static/charts/{chart_id}.png",
        "metadata": {
            "chart_type": chart_type,
            "data_points": len(x_data),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    if format in ("png", "both"):
        fig.write_image(str(png_path), width=width, height=height, scale=2)
        with open(png_path, "rb") as f:
            result["image_base64"] = base64.b64encode(f.read()).decode()
        result["image_path"] = str(png_path)

    return result
