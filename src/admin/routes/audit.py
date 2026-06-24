from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse

from src.admin.dependencies import require_admin
from src.admin.services.audit_service import AuditService

router = APIRouter(prefix="/admin/audit", tags=["admin"])


@router.get("/")
async def list_logs(
    request: Request,
    username: str | None = Query(None),
    event_type: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    ip_address: str | None = Query(None),
    limit: int = Query(1000, le=5000),
    _=Depends(require_admin),
):
    svc = AuditService()
    logs = svc.get_logs(
        username=username,
        event_type=event_type,
        date_from=date_from,
        date_to=date_to,
        ip_address=ip_address,
        limit=limit,
    )
    return {"logs": logs, "total": len(logs)}


@router.get("/stats")
async def audit_stats(
    hours: int = Query(24, le=168),
    _=Depends(require_admin),
):
    svc = AuditService()
    return svc.get_statistics(hours=hours)


@router.get("/export")
async def export_logs(
    request: Request,
    _=Depends(require_admin),
):
    svc = AuditService()
    logs = svc.get_logs(limit=10000)
    csv = svc.export_csv(logs)
    return PlainTextResponse(csv, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit_log.csv"})
