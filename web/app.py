from __future__ import annotations

import asyncio
import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from src.clients.c1_client import C1Client
from src.charts.engine import render_chart
from src.deepseek_client import DeepSeekClient
from src.whatif.engine.simulator import WhatIfSimulator
from src.whatif.models import SimulationRequest

app = FastAPI(title="1C MCP Sales Analyst", version="1.0.0")

BASE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
jinja_env = Environment(loader=FileSystemLoader(str(BASE / "templates")), autoescape=True)

def render(name: str, context: dict | None = None) -> HTMLResponse:
    template = jinja_env.get_template(name)
    html = template.render(**(context or {}))
    return HTMLResponse(html)

c1: C1Client | None = None
ds: DeepSeekClient | None = None
simulator: WhatIfSimulator | None = None


async def get_c1() -> C1Client:
    global c1
    if c1 is None:
        c1 = C1Client()
    return c1


async def get_ds() -> DeepSeekClient:
    global ds
    if ds is None:
        ds = DeepSeekClient()
    return ds


async def get_sim() -> WhatIfSimulator:
    global simulator
    if simulator is None:
        simulator = WhatIfSimulator()
    return simulator


# ---- Pages ----

@app.get("/")
async def dashboard():
    return render("dashboard.html", {"page": "dashboard"})


@app.get("/stock")
async def stock_page():
    return render("stock.html", {"page": "stock"})


@app.get("/sales")
async def sales_page():
    return render("sales.html", {"page": "sales"})


@app.get("/chat")
async def chat_page():
    return render("chat.html", {"page": "chat"})


@app.get("/insights")
async def insights_page():
    sent_dir = Path(__file__).resolve().parent.parent / "data" / "sent_insights"
    insights_list: list[dict[str, Any]] = []
    if sent_dir.exists():
        for p in sorted(sent_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:50]:
            try:
                data = json.loads(p.read_text())
                insights_list.append(data)
            except (json.JSONDecodeError, OSError):
                pass
    return render("insights.html", {"page": "insights", "insights": insights_list})


@app.post("/api/insights/scan")
async def api_insights_scan():
    try:
        from src.insights.detectors.sales_anomaly import SalesAnomalyDetector
        from src.insights.detectors.sales_growth import SalesGrowthDetector
        from src.insights.detectors.stock_shortage import StockShortageDetector
        from src.insights.detectors.inactive_clients import InactiveClientsDetector
        from src.insights.detectors.receivables_alert import ReceivablesAlertDetector
        from src.insights.deduplication.dedup_engine import DedupEngine
        from src.insights.models import TenantInsightsConfig

        config = TenantInsightsConfig()
        config.sales_drop_threshold = 0.0
        config.sales_growth_threshold = 0.0
        config.stock_days_threshold = 999

        detectors = [
            SalesAnomalyDetector(config),
            SalesGrowthDetector(config),
            StockShortageDetector(config),
            InactiveClientsDetector(config),
            ReceivablesAlertDetector(config),
        ]

        count = 0
        dedup = DedupEngine(config)
        for detector in detectors:
            raws = await detector.detect()
            for raw in raws:
                if dedup.should_send(raw):
                    dedup.mark_sent(raw)
                    count += 1

        sent_dir = Path(__file__).resolve().parent.parent / "data" / "sent_insights"
        new_insights = []
        if sent_dir.exists():
            for p in sorted(sent_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                try:
                    new_insights.append(json.loads(p.read_text()))
                except (json.JSONDecodeError, OSError):
                    pass
        return {"count": count, "insights": new_insights}
    except Exception as e:
        return {"error": str(e), "count": 0}


@app.get("/whatif")
async def whatif_page():
    return render("whatif.html", {"page": "whatif"})


# ---- API ----

@app.get("/api/dashboard")
async def api_dashboard():
    client = await get_c1()
    stock, sales, by_mgr = await asyncio.gather(
        client.get_stock(),
        c1.get_sales(date_from=(date.today() - timedelta(days=30)).isoformat(), date_to=date.today().isoformat()),
        c1.get_sales_by_manager(),
    )
    total_stock_qty = sum(s["quantity"] for s in stock)
    total_sales_sum = sum(s["sum"] for s in sales)
    return {
        "stock_count": len(stock),
        "stock_qty": total_stock_qty,
        "sales_sum": total_sales_sum,
        "sales_count": len(sales),
        "managers_count": len(by_mgr),
    }


@app.get("/api/stock")
async def api_stock(nomenclature: str = "", min_quantity: int = 0):
    client = await get_c1()
    data = await client.get_stock(
        nomenclature=nomenclature or None,
        min_quantity=min_quantity or None,
    )
    return {"data": data, "total": len(data)}


@app.get("/api/sales")
async def api_sales(date_from: str = "", date_to: str = "", manager: str = ""):
    client = await get_c1()
    data, by_mgr = await asyncio.gather(
        client.get_sales(date_from=date_from or None, date_to=date_to or None, manager=manager or None),
        client.get_sales_by_manager(date_from=date_from or None, date_to=date_to or None),
    )
    return {"data": data, "total": len(data), "by_manager": by_mgr}


@app.post("/api/chat")
async def api_chat(query: str = ""):
    if not query:
        raise HTTPException(400, "query required")
    ai = await get_ds()
    result = await ai.process_query(query)
    chart_html = ""
    for tc in result["tool_calls"]:
        if tc["name"] == "create_chart" and "result" in tc:
            chart_html = tc["result"].get("html", "")
    return {
        "answer": result["answer"],
        "tool_calls": [{"name": t["name"], "args": t["args"]} for t in result["tool_calls"]],
        "chart_html": chart_html,
        "usage": result["usage"],
    }


@app.post("/api/simulate")
async def api_simulate(
    entity_name: str = "",
    change_percent: float = 10,
    period_days: int = 30,
    scenario_type: str = "price_change",
):
    req = SimulationRequest(
        scenario_type=scenario_type,
        entity_type="nomenclature",
        entity_name=entity_name,
        parameters={"change_percent": change_percent, "period_days": period_days},
    )
    sim = await get_sim()
    result = await sim.simulate(req)
    if not result.baseline.volume:
        return {"error": "Недостаточно данных для симуляции"}
    chart = render_chart(
        "line",
        f"Прогноз: {entity_name} (изменение цены на {change_percent:+.0f}%)",
        result.time_series.dates[:14],
        [result.time_series.baseline[:14], result.time_series.projected[:14]],
        "Дата", "Выручка, ₽",
        series_names=["Базовый", "Прогноз"],
        format="both",
    )
    return {
        "baseline": {"revenue": result.baseline.revenue, "volume": result.baseline.volume, "avg_price": result.baseline.avg_price},
        "projected": {"revenue": result.projected.revenue, "volume": result.projected.volume, "avg_price": result.projected.avg_price},
        "delta": {"revenue_percent": round((result.delta.revenue / result.baseline.revenue) * 100, 1) if result.baseline.revenue else 0},
        "recommendations": result.recommendations,
        "confidence": result.confidence,
        "chart_html": chart["html"],
    }
