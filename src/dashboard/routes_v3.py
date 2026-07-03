from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from src.dashboard.services.dashboard_service import dashboard_repo
from src.dashboard.services.history_service import history_service
from src.dashboard.services.feedback_service import feedback_service
from src.dashboard.storage.models import init_db
from src.dashboard.export.csv_exporter import export_csv
from src.dashboard.export.xlsx_exporter import export_xlsx

router = APIRouter(prefix="/api/v1", tags=["dashboard_v3"])


def _user(request: Request) -> str:
    payload = getattr(request.state, "user", None)
    return payload.sub if payload else "anonymous"


@router.on_event("startup")
async def startup():
    init_db()


# --- Dashboards CRUD ---

@router.post("/dashboards")
async def create_dashboard(body: dict, request: Request):
    user_id = _user(request)
    doc = dashboard_repo.create(owner_id=user_id, title=body.get("title", ""), query=body.get("query", ""), chart_config=body.get("chart_config", {}), description=body.get("description", ""), tags=body.get("tags"), is_public=body.get("is_public", False))
    return {"status": "success", "dashboard": doc}


@router.get("/dashboards")
async def list_dashboards(request: Request, search: str = Query(""), tags: str = Query(""), is_favorite: bool | None = Query(None), page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    user_id = _user(request)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    result = dashboard_repo.list(owner_id=user_id, search=search, tags=tag_list, is_favorite=is_favorite, page=page, per_page=per_page)
    return {"status": "success", **result}


@router.get("/dashboards/{doc_id}")
async def get_dashboard(doc_id: str, request: Request):
    doc = dashboard_repo.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"status": "success", "dashboard": doc}


@router.patch("/dashboards/{doc_id}")
async def update_dashboard(doc_id: str, body: dict, request: Request):
    allowed = {"title", "description", "tags", "is_public", "is_favorite", "chart_config"}
    updates = {k: v for k, v in body.items() if k in allowed}
    doc = dashboard_repo.update(doc_id, **updates)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"status": "success", "dashboard": doc}


@router.delete("/dashboards/{doc_id}")
async def delete_dashboard(doc_id: str, request: Request):
    ok = dashboard_repo.delete(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"status": "deleted"}


# --- History ---

@router.get("/history")
async def list_history(request: Request, search: str = Query(""), limit: int = Query(50, le=500)):
    user_id = _user(request)
    items = history_service.list(user_id=user_id, limit=limit, search=search)
    return {"status": "success", "history": items}


@router.post("/history/{hid}/rerun")
async def rerun_history(hid: str, request: Request):
    item = history_service.get(hid)
    if not item:
        raise HTTPException(status_code=404, detail="History entry not found")
    return {"status": "success", "message": "Re-run the original query via /api/v1/dashboard/generate", "original_query": item.get("query")}


# --- Feedback ---

@router.post("/dashboards/{doc_id}/feedback")
async def submit_feedback(doc_id: str, body: dict, request: Request):
    user_id = _user(request)
    if not dashboard_repo.get(doc_id):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    fb = feedback_service.submit(dashboard_id=doc_id, user_id=user_id, rating=body.get("rating", "positive"), comment=body.get("comment", ""), issue_type=body.get("issue_type"))
    return {"status": "success", "feedback": fb}


# --- Export ---

@router.post("/dashboards/{doc_id}/export")
async def export_dashboard(doc_id: str, body: dict, request: Request):
    doc = dashboard_repo.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    fmt = body.get("format", "csv")
    from fastapi.responses import StreamingResponse
    import io

    if fmt == "csv":
        data = doc.get("chart_config", {}).get("data", [])
        csv_content = export_csv(data)
        return StreamingResponse(io.StringIO(csv_content), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={doc['title']}.csv"})
    elif fmt == "xlsx":
        data = doc.get("chart_config", {}).get("data", [])
        buf = export_xlsx(data, doc)
        return StreamingResponse(iter([buf.getvalue()]), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={doc['title']}.xlsx"})
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")


# --- Analytics ---

@router.get("/analytics/usage")
async def analytics_usage(request: Request):
    return {"status": "success", "period": {"from": "2026-06-03", "to": "2026-07-03"}, "total_queries": 0, "unique_users": 0, "success_rate": 0.0}
