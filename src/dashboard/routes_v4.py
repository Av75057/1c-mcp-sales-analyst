from __future__ import annotations

from typing import Any

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from src.dashboard.composite.service import composite_service, init_db
from src.dashboard.notifications.service import notification_service
from src.dashboard.rbac.service import rbac_service
from src.dashboard.recommendations.service import recommendation_service
from src.dashboard.scheduler.service import scheduler_service
from src.dashboard.services.data_fetcher import fetch_chart_data

router = APIRouter(prefix="/api/v2", tags=["dashboard_v4"])


def _user(request: Request) -> str:
    payload = getattr(request.state, "user", None)
    return payload.sub if payload else "anonymous"


@router.on_event("startup")
async def startup():
    init_db()


# === Composite Dashboards (multi-chart) ===

@router.post("/dashboards")
async def create_composite_dashboard(body: dict, request: Request):
    user_id = _user(request)
    doc = composite_service.create(
        owner_id=user_id,
        title=body.get("title", ""),
        description=body.get("description", ""),
        charts=body.get("charts", []),
        tags=body.get("tags"),
        is_public=body.get("is_public", False),
        refresh_interval_minutes=body.get("refresh_interval_minutes", 0),
        is_favorite=body.get("is_favorite", False),
    )
    return {"status": "success", "dashboard": doc}

@router.get("/dashboards")
async def list_composite_dashboards(request: Request, search: str = Query(""), page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    user_id = _user(request)
    result = composite_service.list(owner_id=user_id, search=search, page=page, per_page=per_page)
    return {"status": "success", **result}


@router.get("/dashboards/{doc_id}")
async def get_composite_dashboard(doc_id: str, request: Request):
    doc = composite_service.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"status": "success", "dashboard": doc}


# === Fetch data for chart config ===

@router.post("/dashboards/fetch-data")
async def fetch_dashboard_data(body: dict):
    """Загрузить данные из 1С по конфигурации графика."""
    chart_config = body.get("chart_config", {})
    if not chart_config:
        raise HTTPException(status_code=400, detail="chart_config required")
    try:
        data = await fetch_chart_data(chart_config)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboards/{doc_id}/refresh")
async def refresh_dashboard_data(doc_id: str):
    """Обновить данные для всех графиков дашборда."""
    doc = composite_service.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    charts = doc.get("charts", [])
    results = []
    for chart in charts:
        try:
            data = await fetch_chart_data(chart.get("chart_config", {}))
            chart["data"] = data
            results.append({"id": chart.get("id", ""), "status": "success", "count": len(data)})
        except Exception as e:
            results.append({"id": chart.get("id", ""), "status": "error", "error": str(e)})
    # Сохранить обновлённые данные
    composite_service.update(doc_id, charts=charts)
    return {"status": "success", "charts": results, "dashboard": composite_service.get(doc_id)}


@router.patch("/dashboards/{doc_id}")
async def update_composite_dashboard(doc_id: str, body: dict, request: Request):
    allowed = {"title", "description", "charts", "tags", "is_public", "is_favorite", "refresh_interval_minutes"}
    updates = {k: v for k, v in body.items() if k in allowed}
    doc = composite_service.update(doc_id, **updates)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"status": "success", "dashboard": doc}


@router.delete("/dashboards/{doc_id}")
async def delete_composite_dashboard(doc_id: str, request: Request):
    ok = composite_service.delete(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"status": "deleted"}


# === Permissions / RBAC ===

@router.post("/dashboards/{doc_id}/permissions")
async def set_dashboard_permission(doc_id: str, body: dict, request: Request):
    user_id = body.get("user_id", "")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    perm = rbac_service.set_permission(doc_id, user_id, body.get("permission", "view"))
    return {"status": "success", "permission": perm}


@router.get("/dashboards/{doc_id}/permissions")
async def list_dashboard_permissions(doc_id: str, request: Request):
    perms = rbac_service.list_permissions(doc_id)
    return {"status": "success", "permissions": perms}


@router.delete("/dashboards/{doc_id}/permissions")
async def remove_dashboard_permission(doc_id: str, body: dict, request: Request):
    user_id = body.get("user_id", "")
    ok = rbac_service.remove_permission(doc_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"status": "deleted"}


@router.get("/dashboards/{doc_id}/access/{user_id}")
async def check_dashboard_access(doc_id: str, user_id: str, required: str = Query("view"), request: Request = None):
    allowed = rbac_service.can_access(doc_id, user_id, required)
    return {"status": "success", "allowed": allowed, "required": required}


# === Scheduler / Reports ===

@router.post("/dashboards/{doc_id}/schedules")
async def create_schedule(doc_id: str, body: dict, request: Request):
    user_id = _user(request)
    doc = composite_service.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    sched = scheduler_service.create(
        dashboard_id=doc_id,
        owner_id=user_id,
        cron=body.get("cron", "0 9 * * 1"),
        recipients=body.get("recipients"),
        format=body.get("format", "csv"),
    )
    return {"status": "success", "schedule": sched}


@router.get("/dashboards/{doc_id}/schedules")
async def list_schedules(doc_id: str, request: Request):
    schedules = scheduler_service.list_by_dashboard(doc_id)
    return {"status": "success", "schedules": schedules}


@router.patch("/schedules/{sid}")
async def update_schedule(sid: str, body: dict, request: Request):
    allowed = {"cron", "recipients", "format", "is_active"}
    updates = {k: v for k, v in body.items() if k in allowed}
    sched = scheduler_service.update(sid, **updates)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "success", "schedule": sched}


@router.delete("/schedules/{sid}")
async def delete_schedule(sid: str, request: Request):
    ok = scheduler_service.delete(sid)
    if not ok:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted"}


# === Notifications ===

@router.get("/notifications")
async def list_notifications(request: Request, unread_only: bool = Query(False), limit: int = Query(50, le=200)):
    user_id = _user(request)
    items = notification_service.list(user_id=user_id, unread_only=unread_only, limit=limit)
    return {"status": "success", "notifications": items, "unread_count": notification_service.unread_count(user_id)}


@router.post("/notifications/{nid}/read")
async def mark_notification_read(nid: str, request: Request):
    ok = notification_service.mark_read(nid)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(request: Request):
    user_id = _user(request)
    count = notification_service.mark_all_read(user_id)
    return {"status": "success", "marked_read": count}


# === Recommendations ===

@router.post("/dashboards/{doc_id}/recommendations")
async def generate_recommendations(doc_id: str, request: Request):
    doc = composite_service.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    recs = recommendation_service.generate(doc_id, doc)
    return {"status": "success", "recommendations": recs}


@router.get("/dashboards/{doc_id}/recommendations")
async def list_recommendations(doc_id: str, request: Request):
    recs = recommendation_service.list(doc_id)
    return {"status": "success", "recommendations": recs}


@router.post("/recommendations/{rid}/apply")
async def apply_recommendation(rid: str, request: Request):
    ok = recommendation_service.mark_applied(rid)
    if not ok:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"status": "applied"}
