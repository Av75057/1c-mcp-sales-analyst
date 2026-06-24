from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.admin.dependencies import require_admin
from src.admin.services.tools_service import ToolsService

router = APIRouter(prefix="/admin/tools", tags=["admin"])


@router.get("/")
async def list_tools(_=Depends(require_admin)):
    svc = ToolsService()
    return {"tools": svc.get_all()}


@router.get("/stats")
async def tool_statistics(hours: int = Query(24, le=168), _=Depends(require_admin)):
    svc = ToolsService()
    return svc.get_statistics(hours=hours)


@router.get("/calls")
async def recent_calls(limit: int = Query(50, le=200), _=Depends(require_admin)):
    svc = ToolsService()
    return {"calls": svc.get_recent_calls(limit=limit)}
