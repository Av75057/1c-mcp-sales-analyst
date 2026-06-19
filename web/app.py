from __future__ import annotations

import asyncio
import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.clients.c1_client import C1Client
from src.charts.engine import render_chart
from src.config import settings
from src.deepseek_client import DeepSeekClient
from src.whatif.engine.simulator import WhatIfSimulator
from src.whatif.models import SimulationRequest

app = FastAPI(title="1C MCP Sales Analyst", version="1.0.0")

BASE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

c1 = C1Client()
ds = DeepSeekClient()
simulator = WhatIfSimulator()


def run_async(coro: Any) -> Any:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---- Pages ----

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "page": "dashboard"})


@app.get("/stock", response_class=HTMLResponse)
async def stock_page(request: Request):
    return templates.TemplateResponse("stock.html", {"request": request, "page": "stock"})


@app.get("/sales", response_class=HTMLResponse)
async def sales_page(request: Request):
    return templates.TemplateResponse("sales.html", {"request": request, "page": "sales"})


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request, "page": "chat"})


@app.get("/insights", response_class=HTMLResponse)
async def insights_page(request: Request):
    sent_dir = Path(__file__).resolve().parent.parent / "data" / "sent_insights"
    insights_list: list[dict[str, Any]] = []
    if sent_dir.exists():
        for p in sorted(sent_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:50]:
            try:
                data = json.loads(p.read_text())
                insights_list.append(data)
            except (json.JSONDecodeError, OSError):
                pass
    return templates.TemplateResponse("insights.html", {"request": request, "page": "insights", "insights": insights_list})


@app.get("/whatif", response_class=HTMLResponse)
async def whatif_page(request: Request):
    return templates.TemplateResponse("whatif.html", {"request": request, "page": "whatif"})


# ---- API ----

@app.get("/api/dashboard")
async def api_dashboard():
    stock, sales, by_mgr = run_async(asyncio.gather(
        c1.get_stock(),
        c1.get_sales(date_from=(date.today() - timedelta(days=30)).isoformat(), date_to=date.today().isoformat()),
        c1.get_sales_by_manager(),
    ))
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
    data = run_async(c1.get_stock(
        nomenclature=nomenclature or None,
        min_quantity=min_quantity or None,
    ))
    return {"data": data, "total": len(data)}


@app.get("/api/sales")
async def api_sales(date_from: str = "", date_to: str = "", manager: str = ""):
    data = run_async(c1.get_sales(
        date_from=date_from or None,
        date_to=date_to or None,
        manager=manager or None,
    ))
    by_mgr = run_async(c1.get_sales_by_manager(
        date_from=date_from or None,
        date_to=date_to or None,
    ))
    return {"data": data, "total": len(data), "by_manager": by_mgr}


@app.post("/api/chat")
async def api_chat(query: str = ""):
    if not query:
        raise HTTPException(400, "query required")
    result = run_async(ds.process_query(query))
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
    request = SimulationRequest(
        scenario_type=scenario_type,
        entity_type="nomenclature",
        entity_name=entity_name,
        parameters={"change_percent": change_percent, "period_days": period_days},
    )
    result = run_async(simulator.simulate(request))
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
