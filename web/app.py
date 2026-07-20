from __future__ import annotations

import asyncio
import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

import numpy as np

from src.admin.database import get_db
from src.cache import CachedC1Client, C1UnavailableError
from src.clients.c1_client import C1Client
from src.config import settings
from src.logger import logger
from src.perf import measure_time
from src.charts.engine import render_chart
from src.deepseek_client import DeepSeekClient
from src.metrics import metrics
from src.whatif.engine.simulator import WhatIfSimulator

from src.observability.middleware import MetricsMiddleware
from src.auth.middleware import AuthMiddleware
from src.data_quality.routes import router as data_quality_router
from src.rag.routes import router as rag_router
from src.events.routes import router as events_router
from src.anonymization.routes import router as anonymization_router
from src.metadata.routes import router as metadata_router
from src.chat.websocket_handler import router as chat_ws_router
from src.dashboard.router import router as dashboard_router
from src.dashboard.routes_v3 import router as dashboard_v3_router
from src.dashboard.routes_v4 import router as dashboard_v4_router
from src.dashboard.routes_v5 import router as dashboard_v5_router
from src.workflows.routes import router as workflows_router
from src.proactive.routes import router as proactive_router
from src.auth.routes import router as auth_router
from src.audit.middleware import AuditMiddleware
from src.audit.logger import audit_logger
from src.security.headers import SecurityHeadersMiddleware
from src.security.rate_limit import init_rate_limiter, limiter

from src.admin.routes.dashboard import router as admin_dashboard_router
from src.admin.routes.users import router as admin_users_router
from src.admin.routes.audit import router as admin_audit_router
from src.admin.routes.monitoring import router as admin_monitoring_router
from src.admin.routes.system import router as admin_system_router
from src.admin.routes.settings import router as admin_settings_router
from src.admin.routes.integrations import router as admin_integrations_router
from src.admin.routes.tools_route import router as admin_tools_router
from src.admin.routes.api_keys import router as admin_api_keys_router
from src.admin.routes.ip_block import router as admin_ip_blocks_router
from src.admin.routes.multitenant import router as multitenant_router
from src.clients.connection_middleware import ConnectionMiddleware


def _convert_numpy(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _convert_numpy(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_convert_numpy(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


# Патч jsonable_encoder для поддержки numpy
import fastapi.encoders as _encoders
_original_je = _encoders.jsonable_encoder

def _patched_je(obj: Any, *args: Any, **kwargs: Any) -> Any:
    return _original_je(_convert_numpy(obj), *args, **kwargs)

_encoders.jsonable_encoder = _patched_je


app = FastAPI(title="1C MCP Sales Analyst", version="1.3.0")


@app.on_event("startup")
async def on_startup():
    from src.admin.database import init_db, async_session
    from src.admin.migrate_users import migrate
    from src.admin.services.settings_service import SettingsService
    from src.chat.repository import ChatBase
    from sqlalchemy import create_engine
    await init_db()
    await migrate()
    async with async_session() as db:
        svc = SettingsService(db)
        await svc.seed_defaults()
    # Init multi-tenant tables
    try:
        from src.admin.multitenant.models import init_multitenant_db
        from src.admin.database import engine as admin_engine
        await init_multitenant_db(admin_engine)
    except Exception as e:
        logger.warning("Multi-tenant DB init failed: {}", e)

    # Init chat tables in same admin DB
    from src.admin.database import engine as admin_engine
    from sqlalchemy import text as _text
    async with admin_engine.begin() as conn:
        await conn.run_sync(ChatBase.metadata.create_all)
        await conn.execute(_text("UPDATE chat_sessions SET is_archived = 0 WHERE is_archived IS NULL"))

    # Start health check background task
    try:
        asyncio.create_task(_health_check_loop())
    except Exception as e:
        logger.warning("Health check task failed: {}", e)

    # Init data lineage DB
    try:
        from src.data_quality.lineage.tracker import lineage_tracker
        await lineage_tracker.init_db()
    except Exception as e:
        logger.warning("Lineage DB init failed: {}", e)

    # Init knowledge base DB
    try:
        from src.rag.repository import init_db as init_knowledge_db
        init_knowledge_db()
    except Exception as e:
        logger.warning("Knowledge DB init failed: {}", e)

    # Init anonymization DB
    try:
        from src.anonymization.storage import init_db as init_anon_db
        init_anon_db()
    except Exception as e:
        logger.warning("Anonymization DB init failed: {}", e)


# Middleware (порядок: от внешнего к внутреннему)
app.add_middleware(MetricsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Логирование 500 ошибок
from starlette.middleware.base import BaseHTTPMiddleware
class ErrorLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error("[500] {} {}: {}", request.method, request.url.path, e)
            import traceback; logger.error("Traceback:\n{}", traceback.format_exc())
            raise
app.add_middleware(ErrorLogMiddleware)
app.add_middleware(ConnectionMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Connection-ID"],
)
if settings.auth_enabled:
    app.add_middleware(AuditMiddleware)
    app.add_middleware(AuthMiddleware)

init_rate_limiter(app)
app.include_router(auth_router)
# Admin routes
app.include_router(admin_dashboard_router)
app.include_router(admin_users_router)
app.include_router(admin_audit_router)
app.include_router(admin_monitoring_router)
app.include_router(admin_settings_router)
app.include_router(admin_integrations_router)
app.include_router(admin_api_keys_router)
app.include_router(admin_ip_blocks_router)
app.include_router(admin_tools_router)
app.include_router(admin_system_router)
app.include_router(multitenant_router)

# Data Quality routes
app.include_router(data_quality_router)
app.include_router(rag_router)
app.include_router(events_router)
app.include_router(workflows_router)
app.include_router(proactive_router)
app.include_router(anonymization_router)
app.include_router(metadata_router)
app.include_router(dashboard_router)
app.include_router(dashboard_v3_router)
app.include_router(dashboard_v4_router)
app.include_router(dashboard_v5_router)
app.include_router(chat_ws_router)

BASE = Path(__file__).resolve().parent

# React SPA — serve built files if they exist
REACT_DIST = BASE.parent / "frontend" / "dist"
if REACT_DIST.exists():
    from fastapi.staticfiles import StaticFiles

    @app.exception_handler(404)
    async def spa_fallback(request: Request, exc):
        if request.url.path.startswith("/api/") or request.url.path.startswith("/ws/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        react_index = REACT_DIST / "index.html"
        if react_index.exists():
            return HTMLResponse(react_index.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>Not Found</h1>", status_code=404)

    app.mount("/assets", StaticFiles(directory=str(REACT_DIST / "assets")), name="react_assets")
    logger.info("[React] SPA enabled: {}", REACT_DIST)

app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
jinja_env = Environment(loader=FileSystemLoader(str(BASE / "templates")), autoescape=True)

def render(name: str, context: dict | None = None) -> HTMLResponse:
    template = jinja_env.get_template(name)
    html = template.render(**(context or {}))
    return HTMLResponse(html)

def render_spa() -> HTMLResponse:
    """Serve React SPA if available, otherwise Jinja2 fallback."""
    REACT_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if REACT_DIST.exists() and (REACT_DIST / "index.html").exists():
        return HTMLResponse((REACT_DIST / "index.html").read_text(encoding="utf-8"))
    return render("dashboard.html", {"page": "dashboard"})

c1: Any | None = None
ds: DeepSeekClient | None = None
simulator: WhatIfSimulator | None = None


async def _health_check_loop():
    try:
        from src.admin.multitenant.health_check import health_check_loop
        await health_check_loop(interval=300)
    except Exception:
        pass


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


# ---- Landing Page ----

LANDING_LEADS: list = []

@app.get("/landing")
async def landing_page():
    return HTMLResponse(Path("web/templates/landing.html").read_text(encoding="utf-8"))


@app.post("/api/landing/lead")
async def landing_lead(body: dict):
    name = body.get("name", "").strip()
    contact = body.get("contact", "").strip()
    config = body.get("config", "").strip()
    comment = body.get("comment", "").strip()

    if not name or not contact or not config:
        raise HTTPException(status_code=400, detail="Заполните обязательные поля")

    from datetime import datetime, timezone
    lead = {"name": name, "contact": contact, "config": config, "comment": comment, "created_at": datetime.now(timezone.utc).isoformat()}
    LANDING_LEADS.append(lead)

    # Уведомление в Telegram
    try:
        from src.dashboard.bot.service import telegram_bot
        text = (
            f"📩 <b>Новая заявка с лендинга</b>\n"
            f"Имя: {name}\n"
            f"Контакт: {contact}\n"
            f"Конфигурация: {config}\n"
            f"Комментарий: {comment}"
        )
        asyncio.ensure_future(telegram_bot.send_message(text))
    except Exception as e:
        logger.warning("[Landing] Telegram notify failed: {}", e)

    logger.info("[Landing] New lead: {} ({}) — {}", name, contact, config)
    return {"status": "success", "message": "Заявка принята"}


@app.get("/api/landing/leads")
async def landing_leads():
    return {"leads": list(reversed(LANDING_LEADS))}


# ---- Pages ----

@app.get("/login")
async def login_page():
    return render_spa()

@app.get("/admin")
async def admin_page():
    return render_spa()

@app.get("/search")
async def search_page():
    return render_spa()

@app.get("/")
async def dashboard():
    REACT_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if REACT_DIST.exists() and (REACT_DIST / "index.html").exists():
        return HTMLResponse((REACT_DIST / "index.html").read_text(encoding="utf-8"))
    return render("dashboard.html", {"page": "dashboard"})


@app.get("/stock")
async def stock_page():
    return render("stock.html", {"page": "stock"})


@app.get("/sales")
async def sales_page():
    return render_spa()


@app.get("/library")
async def library_page(request: Request):
    return render_spa()

@app.get("/library/{doc_id}")
async def library_view_page(doc_id: str, request: Request):
    return render_spa()

@app.get("/dashboards")
async def dashboards_v2_page():
    return render_spa()

@app.get("/chart-test")
async def chart_test_page():
    return render("chart_test.html", {"page": "chart_test"})

@app.get("/chat")
async def chat_page():
    return render_spa()


@app.get("/insights")
async def insights_page():
    return render_spa()


@app.get("/documents")
async def documents_page():
    return render_spa()

# /documents/sales handled by React SPA


@app.get("/status")
async def status_page():
    return render_spa()


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


@app.get("/api/health/performance")
async def api_health_performance():
    """Мониторинг производительности MCP-сервера"""
    return {
        "status": "healthy",
        "metrics": metrics.get_summary(),
        "slow_queries": metrics.get_slow_queries(limit=10),
    }


@app.get("/api/v3/executive-summary")
async def api_executive_summary(period: str = Query("this_month"), organization: str | None = Query(None)):
    from src.mcp.summary_generator import generate_executive_summary
    from src.mcp.kpi_dashboard import get_executive_kpi
    kpi = await get_executive_kpi(period=period, organization=organization)
    result = await generate_executive_summary(period=period, kpi_data=kpi.model_dump(mode="json"), organization=organization)
    return result


@app.get("/api/v3/executive-kpi")
async def api_executive_kpi(
    period: str = Query("this_month", description="Период"),
    organization: str | None = Query(None, description="Фильтр по организации"),
    include_sparklines: bool = Query(True, description="Включать спарклайны"),
    manager: str | None = Query(None, description="Фильтр по менеджеру"),
    category: str | None = Query(None, description="Фильтр по категории"),
    date: str | None = Query(None, description="Фильтр по дате (YYYY-MM-DD)"),
):
    """KPI для панели руководителя (выручка, прибыль, заказы, маржа)."""
    from src.mcp.kpi_dashboard import get_executive_kpi
    result = await get_executive_kpi(
        period=period,  # type: ignore
        organization=organization,
        include_sparklines=include_sparklines,
        manager=manager,
        category=category,
        date=date,
    )
    return result.model_dump(mode="json")


@app.get("/health/live")
async def health_live():
    return {"status": "alive"}


@app.get("/health/ready")
async def health_ready():
    from src.health.checks import check_database, check_c1
    db = await check_database()
    c1 = await check_c1()
    all_ok = db["status"] == "ok" and c1["status"] == "ok"
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=200 if all_ok else 503, content={"status": "ready" if all_ok else "not_ready", "checks": {"database": db, "c1": c1}})


@app.get("/health")
async def health():
    from src.health.checks import all_checks
    from fastapi.responses import JSONResponse
    result = await all_checks()
    status_code = 200 if result["status"] in ("healthy", "degraded") else 503
    return JSONResponse(status_code=status_code, content=result)


@app.get("/metrics")
async def metrics_endpoint():
    from src.observability.metrics import get_metrics
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(get_metrics(), media_type="text/plain; version=0.0.4")


@app.get("/api/admin/circuit-breakers")
async def admin_circuit_breakers():
    from src.resilience.circuit_breaker import deepseek_cb, c1_cb
    return {"circuit_breakers": [deepseek_cb.state_metrics, c1_cb.state_metrics]}


@app.post("/api/admin/circuit-breakers/{name}/reset")
async def admin_circuit_breaker_reset(name: str):
    from src.resilience.circuit_breaker import deepseek_cb, c1_cb
    cbs = {"deepseek": deepseek_cb, "c1": c1_cb}
    cb = cbs.get(name)
    if not cb:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")
    cb.reset()
    return {"status": "reset", "name": name, "new_state": cb.state.value}


@measure_time("api_documents_sales")
@app.get("/api/documents/sales")
async def api_documents_sales(
    date_from: str = "",
    date_to: str = "",
    counterparty: str | None = None,
    sum_min: float | None = None,
    sum_max: float | None = None,
    posted_only: bool = True,
    sort_by: str = "date",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 50,
):
    from src.mcp.documents_tool import get_sales_documents
    return await get_sales_documents(
        date_from=date_from,
        date_to=date_to,
        counterparty=counterparty,
        sum_min=sum_min,
        sum_max=sum_max,
        posted_only=posted_only,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@app.get("/api/documents/sales/{doc_id}/lines")
async def api_document_lines(doc_id: str):
    """Возвращает строки документа реализации (товары)."""
    import datetime
    logger.info("Document lines requested: {}", doc_id)
    date_to = datetime.date.today().isoformat()
    date_from = (datetime.date.today() - datetime.timedelta(days=60)).isoformat()

    # Получаем номер документа
    doc_number = ""
    try:
        from src.mcp.documents_tool import get_sales_documents
        docs = await get_sales_documents(date_from=date_from, date_to=date_to, page_size=50)
        for d in docs.get("documents", []):
            if d.get("id") == doc_id:
                doc_number = d.get("number", "")
                break
    except Exception as e:
        logger.warning("[Lines] could not get doc info: {}", e)

    lines = []

    # Пробуем execute_query — запрос регистра с номером документа
    if doc_number:
        try:
            import httpx
            from src.config import settings
            base = settings.c1_base_url.rstrip("/api").rstrip("/").rstrip("/hs") + "/hs"
            date_limit = date_from[:4]
            query_text = (
                f"ВЫБРАТЬ ПЕРВЫЕ 500 Продажи.Номенклатура, Продажи.Количество, "
                f"Продажи.Сумма, Продажи.Регистратор.Номер "
                f"ИЗ РегистрНакопления.Продажи КАК Продажи "
                f"ГДЕ Продажи.Период >= ДАТАВРЕМЯ({date_limit}, 1, 1) "
                f"УПОРЯДОЧИТЬ ПО Продажи.Период УБЫВ"
            )
            async with httpx.AsyncClient(auth=(settings.c1_username, settings.c1_password), timeout=45) as client:
                resp = await client.post(
                    f"{base}/query/execute",
                    content=query_text.encode("utf-8"),
                    headers={"Content-Type": "text/plain;charset=utf-8"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    rows = data.get("rows", [])
                    cols = data.get("columns", [])
                    if rows and cols:
                        col_map = {c: i for i, c in enumerate(cols)}
                        reg_idx = col_map.get("РегистраторНомер", -1)
                        nom_idx = col_map.get("Номенклатура", -1)
                        qty_idx = col_map.get("Количество", -1)
                        sum_idx = col_map.get("Сумма", -1)
                        for r in rows:
                            if reg_idx >= 0 and str(r[reg_idx]) == doc_number:
                                lines.append({
                                    "nomenclature": r[nom_idx] if nom_idx >= 0 else "",
                                    "quantity": r[qty_idx] if qty_idx >= 0 else 0,
                                    "sum": r[sum_idx] if sum_idx >= 0 else 0,
                                    "document_number": r[reg_idx] if reg_idx >= 0 else "",
                                })
                        lines = lines[:15]
                        if lines:
                            logger.info("[Lines] execute_query OK for doc {}", doc_number)
        except Exception as e:
            logger.warning("[Lines] execute_query failed: {}", e)

    # Fallback
    if not lines:
        try:
            from src.clients.c1_client import C1Client
            client = C1Client()
            try:
                sales = await client.get_sales(date_from=date_from, date_to=date_to)
                if sales:
                    lines = [s for s in sales if s.get("document_number") == doc_number]
                    if not lines:
                        lines = [s for s in sales if (s.get("quantity") or 0) > 0 or (s.get("sum") or 0) > 0]
                    lines = lines[:15]
            finally:
                await client.close()
        except Exception as e:
            logger.warning("[Lines] get_sales failed: {}", e)

    return {"status": "success", "lines": lines}

    return {"status": "success", "lines": lines}


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
    return render_spa()


@app.get("/forecast")
async def forecast_page():
    return render("forecast.html", {"page": "forecast"})


@app.get("/whatif")
async def whatif_page():
    return render_spa()


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
            sales = await asyncio.wait_for(client.get_sales(date_from=date_from or None, date_to=date_to or None, limit=100000), timeout=30.0)
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


def _get_chat_user(request: Request) -> str:
    payload = getattr(request.state, "user", None)
    return payload.sub if payload else "anonymous"


# --- Chat API Routes ---

@app.get("/api/chat/sessions")
async def chat_list_sessions(request: Request, db: AsyncSession = Depends(get_db)):
    from src.chat.service import ChatService
    user_id = _get_chat_user(request)
    svc = ChatService(db)
    sessions = await svc.repo.list_sessions(user_id=user_id)
    return {"sessions": sessions}


@app.post("/api/chat/sessions")
async def chat_create_session(request: Request, db: AsyncSession = Depends(get_db)):
    from src.chat.service import ChatService
    _get_chat_user
    user_id = _get_chat_user(request)
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    svc = ChatService(db)
    session = await svc.repo.create_session(user_id=user_id, title=body.get("title", "Новый чат"))
    return {"id": session.id, "title": session.title, "created_at": session.created_at.isoformat()}


@app.get("/api/chat/sessions/{session_id}")
async def chat_get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    from src.chat.repository import ChatRepository
    repo = ChatRepository(db)
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"id": session.id, "title": session.title, "created_at": session.created_at.isoformat(), "updated_at": session.updated_at.isoformat(), "is_archived": session.is_archived}


@app.put("/api/chat/sessions/{session_id}")
async def chat_update_session(session_id: str, body: dict, db: AsyncSession = Depends(get_db)):
    from src.chat.repository import ChatRepository
    repo = ChatRepository(db)
    ok = await repo.update_session(session_id, **{k: v for k, v in body.items() if k in ("title", "is_archived")})
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Updated"}


@app.delete("/api/chat/sessions/{session_id}")
async def chat_delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    from src.chat.repository import ChatRepository
    repo = ChatRepository(db)
    ok = await repo.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Deleted"}


@app.get("/api/chat/sessions/{session_id}/messages")
async def chat_get_messages(session_id: str, page: int = Query(1, ge=1), limit: int = Query(50, le=200), db: AsyncSession = Depends(get_db)):
    from src.chat.repository import ChatRepository
    repo = ChatRepository(db)
    messages, total = await repo.get_messages(session_id, page=page, limit=limit)
    msg_list = []
    for m in messages:
        tool_calls = await repo.get_tool_calls(m.id) if m.role == "assistant" else []
        msg_list.append({"id": m.id, "role": m.role, "content": m.content, "tokens_used": m.tokens_used, "response_time_ms": m.response_time_ms, "created_at": m.created_at.isoformat(), "tool_calls": tool_calls})
    return {"messages": msg_list, "total": total, "page": page, "pages": max(1, (total + limit - 1) // limit)}


@app.post("/api/chat/sessions/{session_id}/messages")
async def chat_send_message(session_id: str, body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    from src.chat.service import ChatService
    _get_chat_user
    user_id = _get_chat_user(request)
    content = body.get("content", "")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Message content is required")
    svc = ChatService(db)
    return await svc.process_message(session_id=session_id, user_id=user_id, content=content)


@app.get("/api/chat/search")
async def chat_search(q: str = Query(""), session_id: str | None = Query(None), limit: int = Query(50, le=200), request: Request = None, db: AsyncSession = Depends(get_db)):
    if not q.strip():
        return {"results": []}
    from src.chat.repository import ChatRepository
    _get_chat_user
    user_id = _get_chat_user(request)
    repo = ChatRepository(db)
    results = await repo.search_messages(user_id=user_id, query=q, session_id=session_id, limit=limit)
    return {"results": results, "total": len(results)}


@app.get("/api/chat/sessions/{session_id}/export")
async def chat_export_session(session_id: str, db: AsyncSession = Depends(get_db)):
    from src.chat.repository import ChatRepository
    repo = ChatRepository(db)
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages, _ = await repo.get_messages(session_id, page=1, limit=10000)
    return {"session": {"id": session.id, "title": session.title, "created_at": session.created_at.isoformat()}, "messages": [{"role": m.role, "content": m.content, "tokens_used": m.tokens_used} for m in messages]}


@app.post("/api/search/reindex")
async def api_search_reindex():
    import traceback
    from src.search.fts_cache import init, refresh
    from src.clients.c1_client import C1Client
    from src.logger import logger
    from datetime import date, timedelta

    init()
    import asyncio
    try:
        c1 = C1Client()
        try:
            items: list[dict] = []
            seen: set[str] = set()

            # Build from stock
            try:
                stock = await asyncio.wait_for(c1.get_stock(), timeout=15.0)
                for s in stock:
                    name = s.get("nomenclature", "")
                    qty = s.get("quantity", 0)
                    if name and name not in seen:
                        seen.add(name)
                        items.append({"name": name, "stock_qty": float(qty), "ref": name})
            except Exception as e:
                logger.warning("Reindex stock fetch failed: {}", e)

            # Enrich with prices from sales (last 7 days only for speed)
            try:
                sales = await asyncio.wait_for(
                    c1.get_sales(
                        date_from=(date.today() - timedelta(days=7)).isoformat(),
                        date_to=date.today().isoformat(),
                    ),
                    timeout=15.0,
                )
                price_map: dict[str, float] = {}
                for s in sales:
                    name = s.get("nomenclature", "")
                    sprice = s.get("sum", 0)
                    sqty = s.get("quantity", 0)
                    if name and float(sqty) > 0:
                        price_map[name] = float(sprice) / float(sqty)
                for item in items:
                    name = item.get("name", "")
                    if name in price_map:
                        item["price"] = round(price_map[name], 2)
            except asyncio.TimeoutError:
                logger.warning("Reindex sales fetch timed out")
            except Exception as e:
                logger.warning("Reindex price enrichment failed: {}", e)
        finally:
            await c1.close()

        if not items:
            return {"status": "error", "message": "No items received"}
        count = refresh(items)
        try:
            from src.search.autocomplete import autocomplete
            autocomplete.build(items)
        except Exception:
            pass
        return {"status": "ok", "items_count": count}
    except Exception as e:
        logger.error("Reindex failed: {}\n{}", e, traceback.format_exc())
        return {"status": "error", "message": str(e)}


@app.post("/api/search/nomenclature")
async def api_search_nomenclature(body: dict):
    from src.search.models import SearchRequest, SearchFilters
    from src.search.service import search_nomenclature
    filters = SearchFilters(**body.get("filters", {}))
    request = SearchRequest(query=body.get("query", ""), strategy=body.get("strategy", "hybrid"), filters=filters, page=body.get("page", 1), limit=body.get("limit", 50))
    result = await search_nomenclature(request)
    return result.model_dump()


@app.get("/api/search/autocomplete")
async def api_search_autocomplete(q: str = "", limit: int = Query(10, le=20)):
    from src.search.autocomplete import autocomplete
    await autocomplete.ensure_built()
    suggestions = autocomplete.suggest(prefix=q, limit=limit)
    return {"suggestions": suggestions, "query": q}


@app.get("/api/search/synonyms")
async def api_search_synonyms():
    from src.search.synonyms import get_all, add, remove
    return {"synonyms": get_all()}


@app.post("/api/search/synonyms")
async def api_search_synonyms_add(body: dict):
    from src.search.synonyms import add
    add(body.get("word", ""), body.get("synonyms", []))
    return {"message": "Added"}


@app.delete("/api/search/synonyms/{word}")
async def api_search_synonyms_delete(word: str):
    from src.search.synonyms import remove
    remove(word)
    return {"message": "Deleted"}


@app.get("/api/search/analytics/top")
async def api_search_analytics_top(days: int = 7, limit: int = 20):
    from src.search.analytics import top_queries, total_count
    return {"queries": top_queries(days=days, limit=limit), "total": total_count(days=days)}


@app.get("/api/search/analytics/no-results")
async def api_search_analytics_no_results(days: int = 7, limit: int = 20):
    from src.search.analytics import no_results_queries
    return {"queries": no_results_queries(days=days, limit=limit)}


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
