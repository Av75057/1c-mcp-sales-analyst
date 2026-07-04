from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from src.dashboard.analytics_service import dashboard_analytics
from src.dashboard.cache.metadata_cache import metadata_cache
from src.dashboard.cache.query_cache import query_cache
from src.dashboard.composite.service import composite_service
from src.dashboard.export.csv_exporter import export_csv
from src.dashboard.export.pdf_exporter import export_pdf
from src.dashboard.export.xlsx_exporter import export_xlsx
from src.dashboard.search import dashboard_search
from src.dashboard.services.data_fetcher import fetch_chart_data
from src.dashboard.share_service import share_service

router = APIRouter(prefix="/api/v3", tags=["dashboard_v5"])


def _user(request: Request) -> str:
    payload = getattr(request.state, "user", None)
    return payload.sub if payload else "anonymous"


# === FTS5 Search ===

@router.get("/search")
async def search_dashboards(q: str = Query(""), limit: int = Query(20, le=100)):
    if not q or not q.strip():
        return {"status": "success", "results": [], "query": q, "count": 0}
    # Сначала пробуем FTS5
    results = dashboard_search.search(q, limit=limit)
    if results:
        return {"status": "success", "results": results, "query": q, "count": len(results)}

    # Fallback: LIKE поиск по таблицам
    from src.dashboard.composite.service import _get_db
    conn = _get_db()
    try:
        # Собираем все записи из обеих таблиц и фильтруем в Python
        # (SQLite не поддерживает Unicode case-insensitive для LIKE)
        rows = conn.execute(
            "SELECT id, title, description, '' as tags FROM composite_dashboards ORDER BY updated_at DESC LIMIT 200"
        ).fetchall()
        results = [{"dashboard_id": r["id"], "title": r["title"], "description": r["description"], "tags": "", "rank": 0} for r in rows]
        try:
            old = conn.execute(
                "SELECT id, title, description, tags FROM dashboards ORDER BY updated_at DESC LIMIT 200"
            ).fetchall()
            for r in old:
                results.append({"dashboard_id": r["id"], "title": r["title"], "description": r["description"], "tags": r.get("tags", "") or "", "rank": 0})
        except Exception:
            pass

        # Фильтр в Python (Unicode-friendly + базовая словоформа)
        def word_matches(word: str, text: str) -> bool:
            if word in text:
                return True
            # Убираем окончания для русского
            if len(word) > 4:
                for suffix in ['ить', 'ать', 'ять', 'ить', 'ить', 'а', 'я', 'ь', 'и', 'й', 'е']:
                    if word.endswith(suffix) and len(word) > len(suffix):
                        stem = word[:-len(suffix)]
                        if stem in text:
                            return True
                        if len(stem) > 3:
                            for s2 in ['а', 'я', 'ь', 'и']:
                                if stem + s2 in text:
                                    return True
            return False

        q_lower = q.lower()
        search_words = [w for w in q_lower.split() if len(w) >= 2]
        filtered = []
        for r in results:
            text = f"{r.get('title', '')} {r.get('description', '')} {r.get('tags', '')}".lower()
            if all(word_matches(w, text) for w in search_words):
                filtered.append(r)
                if len(filtered) >= limit:
                    break
        results = filtered
    finally:
        conn.close()

    return {"status": "success", "results": results, "query": q, "count": len(results)}


@router.post("/search/rebuild")
async def rebuild_search_index():
    dashboard_search.rebuild()
    return {"status": "success", "message": "Search index rebuilt"}


# === Export ===

@router.post("/dashboards/{doc_id}/export")
async def export_dashboard(doc_id: str, body: dict, request: Request):
    doc = composite_service.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    fmt = body.get("format", "csv")
    options = body.get("options", {})
    data = doc.get("charts", [{}])[0].get("data", [])
    meta = {"title": doc.get("title", ""), "description": doc.get("description", ""), "original_query": ""}

    dashboard_analytics.increment_exports()

    if fmt == "csv":
        csv_content = export_csv(data)
        return Response(content=csv_content, media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={doc['title']}.csv"})

    elif fmt == "xlsx":
        buf = export_xlsx(data, meta)
        return Response(content=buf.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={doc['title']}.xlsx"})

    elif fmt == "pdf":
        chart_image = body.get("chart_image_base64")
        buf = await export_pdf(data, meta, chart_image, options)
        return Response(content=buf.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={doc['title']}.pdf"})

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}. Supported: csv, xlsx, pdf")


# === Share ===

@router.post("/dashboards/{doc_id}/share")
async def create_share_link(doc_id: str, body: dict, request: Request):
    doc = composite_service.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    user_id = _user(request)
    share = share_service.create(
        dashboard_id=doc_id,
        shared_by=user_id,
        permissions=body.get("permissions", "view"),
        expires_in_days=body.get("expires_in_days", 30),
    )
    return {"status": "success", "share": share}


@router.get("/shares/{dashboard_id}")
async def list_shares(dashboard_id: str, request: Request):
    shares = share_service.list_for_dashboard(dashboard_id)
    return {"status": "success", "shares": shares}


@router.delete("/shares/{share_id}")
async def revoke_share(share_id: str, request: Request):
    ok = share_service.revoke(share_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Share not found")
    return {"status": "deleted"}


# === Cache ===

@router.get("/cache/metadata")
async def get_metadata_cache_stats():
    return {"status": "success", **metadata_cache.stats()}


@router.get("/cache/query")
async def get_query_cache_stats():
    return {"status": "success", **query_cache.stats()}


@router.delete("/cache/metadata")
async def invalidate_metadata_cache(entity: str = Query("")):
    metadata_cache.invalidate(entity if entity else None)
    return {"status": "invalidated"}


@router.delete("/cache/query")
async def invalidate_query_cache(entity: str = Query("")):
    query_cache.invalidate(entity if entity else None)
    return {"status": "invalidated"}


# === Analytics ===

@router.get("/analytics")
async def get_dashboard_analytics(days: int = Query(30, ge=1, le=365)):
    stats = dashboard_analytics.overview(days=days)
    return {"status": "success", **stats}


# === Public share view (HTML) ===

@router.get("/share/{token}", include_in_schema=False)
async def view_shared_dashboard(token: str, request: Request):
    share = share_service.get_by_token(token)
    if not share:
        from fastapi.responses import HTMLResponse
        html = "<html><body style='background:#1a1d23;color:#e5e7eb;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif'><div style='text-align:center'><h1>🔗</h1><h2>Ссылка недействительна</h2><p>Срок действия ссылки истёк или она была отозвана.</p></div></body></html>"
        return HTMLResponse(content=html, status_code=410)

    doc = composite_service.get(share["dashboard_id"])
    if not doc:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content="<html><body><h1>Дашборд не найден</h1></body></html>", status_code=404)

    charts_html = ""
    charts = doc.get("charts", [])
    for c in charts:
        cfg = c.get("chart_config", {})
        ct = cfg.get("chart_type", "bar")
        charts_html += f"""
        <div class="card">
            <h4>{c.get('title', 'График')} <span class="badge">{ct}</span></h4>
            <div style="height:300px;background:#111318;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#6b7280">
                <span>📊 Данные дашборда «{doc.get('title', '')}»</span>
            </div>
        </div>"""

    from fastapi.responses import HTMLResponse
    html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{doc.get('title', 'Дашборд')} — общий доступ</title>
<style>body{{background:#1a1d23;color:#e5e7eb;font-family:'Segoe UI',sans-serif;padding:20px;max-width:1200px;margin:0 auto}}
.header{{text-align:center;margin-bottom:30px;border-bottom:1px solid #2d3139;padding-bottom:20px}}
h1{{font-size:24px;margin:0}} .badge{{background:#2563eb;color:#fff;padding:2px 10px;border-radius:10px;font-size:12px}}
.card{{background:#1a1d23;border:1px solid #2d3139;border-radius:8px;padding:16px;margin-bottom:16px}}
.meta{{color:#6b7280;font-size:12px;text-align:center;margin-top:30px}}
.footer{{text-align:center;color:#4b5563;font-size:11px;margin-top:40px;border-top:1px solid #2d3139;padding-top:20px}}
</style></head><body>
<div class="header"><h1>📊 {doc.get('title', 'Дашборд')}</h1>
<p style="color:#6b7280">{doc.get('description', '')}</p>
<p class="meta">Просмотр · Доступ по ссылке · {share.get('permissions', 'view')}</p></div>
{charts_html}
<div class="footer">Сгенерировано 1С Аналитиком · {share.get('created_at', '')}</div>
</body></html>"""
    return HTMLResponse(content=html)
