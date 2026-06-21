from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from src.charts.engine import render_chart as engine_render
from src.logger import logger
from src.whatif.charts.file_manager import ChartFileManager


class WhatIfChartRenderer:
    def __init__(self, charts_dir: str = "./static/charts") -> None:
        self.fm = ChartFileManager(charts_dir)

    def render(self, chart_params: dict[str, Any], fmt: str = "both") -> dict[str, Any]:
        ct = chart_params.get("chart_type", "line")
        title = chart_params.get("title", "")
        xd = chart_params.get("x_data", [])
        yd = chart_params.get("y_data", [])
        xl = chart_params.get("x_label", "")
        yl = chart_params.get("y_label", "")
        sn = chart_params.get("series_names")
        cs = chart_params.get("color_scheme", "default")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw = json.dumps(chart_params, sort_keys=True, default=str)
        cid = f"chart_{ts}_{hashlib.md5(raw.encode()).hexdigest()[:8]}"

        engine_fmt = "png" if fmt == "png" else "both"
        result = engine_render(ct, title, xd, yd, xl, yl, series_names=sn, color_scheme=cs, format=engine_fmt)

        out: dict[str, Any] = {
            "chart_id": cid,
            "metadata": {"chart_type": ct, "title": title, "created_at": ts},
        }

        if engine_fmt in ("png", "both"):
            src = result.get("image_path", "")
            if src:
                dst = self.fm.png_path(cid)
                import shutil
                shutil.copy2(src, dst)
                out["png_path"] = str(dst)
                out["image_url"] = f"/static/charts/{self.fm._date_dir().name}/{dst.name}"
                out["image_base64"] = self.fm.read_base64(dst)

        out["html"] = result.get("html", "")
        if result.get("html"):
            hpath = self.fm.html_path(cid)
            hpath.write_text(result["html"], encoding="utf-8")
            out["html_path"] = str(hpath)

        return out

    def render_from_simulation(self, sim_result: dict[str, Any]) -> dict[str, Any] | None:
        cp = sim_result.get("chart_params")
        if not cp:
            return None
        return self.render(cp)
