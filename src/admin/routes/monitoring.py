from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from src.admin.dependencies import require_admin
from src.admin.services.metrics_service import MetricsService
from src.metrics import metrics

router = APIRouter(prefix="/admin/monitoring", tags=["admin"])


@router.get("/")
async def monitoring(_=Depends(require_admin)):
    svc = MetricsService()
    return {
        "dashboard": svc.get_dashboard(),
        "alerts": svc.get_alerts(),
        "slow_queries": svc.get_slow_queries(limit=20),
        "endpoint_stats": svc.get_endpoint_stats(),
        "summary": metrics.get_summary(),
    }
