from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from src.data_quality.lineage.tracker import lineage_tracker
from src.data_quality.monitoring.dashboard import compute_quality_report
from src.data_quality.validation.contracts import TOOL_CONTRACTS

router = APIRouter(prefix="/api/data", tags=["data_quality"])


@router.get("/quality/report")
async def quality_report(request: Request, period: str = Query("24h", description="Период отчёта")):
    return {"period": period, "message": "Data quality report. Run POST /api/search/nomenclature to generate data first."}


@router.get("/quality/anomalies")
async def quality_anomalies():
    return {"total_anomalies": 0, "anomalies": []}


@router.get("/lineage")
async def get_lineage(source_endpoint: str | None = Query(None), limit: int = Query(100, le=1000)):
    records = await lineage_tracker.get_lineage(source_endpoint=source_endpoint, limit=limit)
    return {"records": records, "total": len(records)}


@router.post("/lineage/cleanup")
async def cleanup_lineage(days_old: int = Query(30, description="Удалять записи старше N дней")):
    deleted = await lineage_tracker.cleanup(days_old=days_old)
    return {"deleted": deleted}


@router.get("/contracts")
async def get_contracts():
    contracts = []
    for name, contract in TOOL_CONTRACTS.items():
        contracts.append({"tool_name": name, "output_model": contract["output_model"].__name__, "quality_rules": contract["quality_rules"]})
    return {"contracts": contracts}


@router.get("/lineage/init")
async def init_lineage_db():
    await lineage_tracker.init_db()
    return {"status": "ok"}
