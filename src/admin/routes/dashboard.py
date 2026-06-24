from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from src.admin.dependencies import require_admin
from src.admin.services.metrics_service import MetricsService
from src.admin.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/")
async def admin_dashboard(request: Request, _=Depends(require_admin)):
    metrics_svc = MetricsService()
    audit_svc = AuditService()
    return {
        "metrics": metrics_svc.get_dashboard(),
        "alerts": metrics_svc.get_alerts(),
        "audit_stats": audit_svc.get_statistics(hours=24),
        "slow_queries": metrics_svc.get_slow_queries(limit=5),
    }
