from __future__ import annotations

import asyncio
import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from src.cache import CachedC1Client, C1UnavailableError
from src.clients.c1_client import C1Client
from src.logger import logger
from src.perf import measure_time
from src.charts.engine import render_chart
from src.deepseek_client import DeepSeekClient
from src.whatif.engine.simulator import WhatIfSimulator

app = FastAPI(title="1C MCP Sales Analyst", version="1.0.0", default_response_class=ORJSONResponse)

BASE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
jinja_env = Environment(loader=FileSystemLoader(str(BASE / "templates")), autoescape=True)

def render(name: str, context: dict | None = None) -> HTMLResponse:
    template = jinja_env.get_template(name)
    html = template.render(**(context or {}))
    return HTMLResponse(html)

c1: Any | None = None
ds: DeepSeekClient | None = None
simulator: WhatIfSimulator | None = None


async def get_c1() -> C1Client:
    global c1
    if c1 is None:
        real_client = C1Client()
        c1 = CachedC1Client(real_client, ttl=30)  # type: ignore
    return c1  # type: ignore


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


@app.get("/documents")
async def documents_page():
    return render("documents.html", {"page": "documents"})


@app.get("/status")
async def status_page():
    return render("status.html", {"page": "status"})


@measure_time("api_status")
@app.get("/api/status")
async def api_status():
    import os
    insights_dir = Path(__file__).resolve().parent.parent / "data" / "sent_insights"
    insights_count = len(list(insights_dir.glob("*.json"))) if insights_dir.exists() else 0
    status_data = {
        "stock_count": 0,
        "sales_count": 0,
        "sales_sum": 0,
        "insights_count": insights_count,
        "deepseek_key": bool(os.getenv("DEEPSEEK_API_KEY")),
        "telegram_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "mock_mode": bool(os.getenv("USE_MOCK_DATA", "false") == "true"),
        "c1_url": os.getenv("C1_BASE_URL", "http://localhost/1c/api"),
        "llm_model": os.getenv("LLM_MODEL", "deepseek-chat"),
        "port": os.getenv("PORT", "8080"),
        "uptime": "работает",
        "c1_connected": False,
    }
    try:
        client = await get_c1()
        stock_coro = asyncio.wait_for(client.get_stock(), timeout=5.0)
        sales_coro = asyncio.wait_for(client.get_sales(), timeout=5.0)
        results = await asyncio.gather(stock_coro, sales_coro, return_exceptions=True)
        stock_res, sales_res = results
        if isinstance(stock_res, list):
            status_data["stock_count"] = len(stock_res)
        if isinstance(sales_res, list):
            status_data["sales_count"] = len(sales_res)
            status_data["sales_sum"] = sum(s.get("sum", 0) for s in sales_res)
        status_data["c1_connected"] = isinstance(stock_res, list) or isinstance(sales_res, list)
    except Exception:
        status_data["c1_connected"] = False
    return status_data


@app.post("/api/documents/upload")
async def api_documents_upload(file: UploadFile = File(...), match_nomenclature: bool = Form(False)):
    try:
        if not file.filename:
            return {"status": "failed", "error": "Файл не выбран"}
        data = await file.read()
        if len(data) == 0:
            return {"status": "failed", "error": "Пустой файл"}
        from src.docparser.engine import DocParserEngine
        engine = DocParserEngine()
        catalog = None
        if match_nomenclature:
            from src.clients.mock_c1_client import MockC1Client
            mock = MockC1Client()
            items = await mock.list_nomenclature("", limit=200)
            catalog = [{"id": i["ref"], "name": i["name"]} for i in items]
        result = await engine.parse_with_matching(file.filename, data, nomenclature_catalog=catalog) if catalog else await engine.parse(file.filename, data)
        return result
    except Exception as e:
        return {"status": "failed", "error": str(e)}


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
        import asyncio

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

        async def safe_detect(detector):
            try:
                raws = await asyncio.wait_for(detector.detect(), timeout=15.0)
                return raws
            except asyncio.TimeoutError:
                logger.warning("Детектор {} превысил таймаут", detector.__class__.__name__)
            except Exception as e:
                logger.warning("Детектор {} ошибка: {}", detector.__class__.__name__, e)
            return []

        results = await asyncio.wait_for(
            asyncio.gather(*(safe_detect(d) for d in detectors)),
            timeout=20.0,
        )
        for raws in results:
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


@app.get("/analysis/abc-xyz")
async def abc_xyz_page():
    return render("abc_xyz.html", {"page": "abc_xyz"})


@app.get("/forecast")
async def forecast_page():
    return render("forecast.html", {"page": "forecast"})


@app.get("/whatif")
async def whatif_page():
    return render("whatif.html", {"page": "whatif"})


# ---- API ----

@app.get("/api/dashboard")
async def api_dashboard():
    client = await get_c1()
    stock, sales, by_mgr = await asyncio.gather(
        client.get_stock(),
        client.get_sales(date_from=(date.today() - timedelta(days=30)).isoformat(), date_to=date.today().isoformat()),
        client.get_sales_by_manager(),
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


@measure_time("api_stock")
@app.get("/api/stock")
async def api_stock(nomenclature: str = "", min_quantity: int = 0):
    client = await get_c1()
    try:
        data = await client.get_stock(
            nomenclature=nomenclature or None,
            min_quantity=min_quantity or None,
        )
        return {"data": data, "total": len(data)}
    except C1UnavailableError:
        return {"data": [], "total": 0}


@measure_time("api_forecast_sales")
@app.get("/api/forecast/sales")
async def api_forecast_sales(nomenclature: str = "", days: int = 30, method: str = "auto"):
    from src.forecasting.tool import forecast_sales_tool
    return await forecast_sales_tool(nomenclature=nomenclature, days=days, method=method)


@measure_time("api_forecast_stockout")
@app.get("/api/forecast/stockout")
async def api_forecast_stockout(lead_time: int = 7, safety_stock: int = 3):
    from src.forecasting.tool import forecast_stockout_tool
    return await forecast_stockout_tool(lead_time_days=lead_time, safety_stock_days=safety_stock)


@measure_time("api_abc_xyz")
@app.get("/api/analysis/abc-xyz")
async def api_abc_xyz(date_from: str = "", date_to: str = "", group_by: str = "nomenclature"):
    try:
        from src.analysis.abc_xyz import analyze
        client = await get_c1()
        try:
            sales = await asyncio.wait_for(client.get_sales(date_from=date_from or None, date_to=date_to or None), timeout=30.0)
        except asyncio.TimeoutError:
            return {"error": "Таймаут загрузки данных из 1С"}
        if not sales:
            return {"error": "Нет данных о продажах за указанный период"}
        result = analyze(sales, date_from=date_from, date_to=date_to, group_by=group_by)
        return {"summary": result.summary, "matrix": result.matrix, "recommendations": result.recommendations}
    except Exception as e:
        return {"error": str(e)}


@measure_time("api_nomenclature")
@app.get("/api/nomenclature")
async def api_nomenclature(query: str = ""):
    client = await get_c1()
    try:
        data = await client.list_nomenclature(query=query or "", limit=50)
        return {"data": data, "total": len(data)}
    except C1UnavailableError:
        return {"data": [], "total": 0}


@measure_time("api_sales")
@app.get("/api/sales")
async def api_sales(date_from: str = "", date_to: str = "", manager: str = ""):
    client = await get_c1()
    try:
        data, by_mgr = await asyncio.gather(
            client.get_sales(date_from=date_from or None, date_to=date_to or None, manager=manager or None),
            client.get_sales_by_manager(date_from=date_from or None, date_to=date_to or None),
        )
        return {"data": data, "total": len(data), "by_manager": by_mgr}
    except C1UnavailableError:
        return {"data": [], "total": 0, "by_manager": []}


@app.post("/api/chat")
async def api_chat(query: str = Form("")):
    if not query:
        return {"answer": "Введите запрос"}
    try:
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
    except asyncio.TimeoutError:
        return {"answer": "⏱️ Превышено время ожидания. Попробуйте упростить запрос или повторить позже."}
    except Exception as e:
        return {"answer": f"❌ Ошибка: {e}"}


@app.post("/api/simulate")
async def api_simulate(
    scenario_type: str = Form("price_change"),
    entity_name: str = Form(""),
    change_percent: float = Form(None),
    period_days: int = Form(30),
    discount_percent: float = Form(None),
    promotion_days: int = Form(None),
    order_size_change_percent: float = Form(None),
    employee_name: str = Form(None),
    monthly_revenue: float = Form(None),
    years_in_company: int = Form(None),
):
    from src.whatif.mcp.tools import simulate_scenario_tool as sim_tool
    kwargs = {"scenario_type": scenario_type, "entity_name": entity_name}
    if change_percent is not None:
        kwargs["change_percent"] = change_percent
    if period_days:
        kwargs["period_days"] = period_days
    if discount_percent is not None:
        kwargs["discount_percent"] = discount_percent
    if promotion_days:
        kwargs["promotion_days"] = promotion_days
    if order_size_change_percent is not None:
        kwargs["order_size_change_percent"] = order_size_change_percent
    if employee_name:
        kwargs["employee_name"] = employee_name
    if monthly_revenue is not None:
        kwargs["monthly_revenue"] = monthly_revenue
    if years_in_company is not None:
        kwargs["years_in_company"] = years_in_company

    result = await sim_tool(**kwargs)
    if not result.get("success"):
        return {"error": result.get("error", "Ошибка симуляции")}

    b = result.get("baseline_metrics", {})
    p = result.get("projected_metrics", {})
    d = result.get("delta_percent", {})
    rev = d.get("revenue", 0)

    baseline_rev = b.get("revenue", b.get("daily_revenue", 0)) * (period_days or 30)
    projected_rev = p.get("revenue", p.get("daily_revenue", 0)) * (period_days or 30)

    margin = 0.4
    bm = baseline_rev * margin
    pm = projected_rev * margin

    chart_data = result.get("chart_params")
    chart_html = ""
    if chart_data:
        try:
            xd = (chart_data.get("x_data") or [])[:14]
            yd = chart_data.get("y_data") or []
            if yd and isinstance(yd[0], list):
                yd = [s[:14] for s in yd]
            elif yd:
                yd = yd[:14]
            chart = render_chart(chart_data.get("chart_type", "line"), chart_data.get("title", "Прогноз"), xd, yd, chart_data.get("x_label", ""), chart_data.get("y_label", ""), series_names=chart_data.get("series_names"), format="both")
            chart_html = chart["html"]
        except Exception:
            pass

    return {
        "baseline": {"revenue": baseline_rev, "margin": bm},
        "projected": {"revenue": projected_rev, "margin": pm},
        "delta": {"revenue_percent": rev, "margin_percent": d.get("margin", 0)},
        "recommendations": result.get("recommendations", []),
        "confidence": result.get("confidence", 0),
        "use_real_data": result.get("use_real_data", False),
        "chart_html": chart_html,
    }
