from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.database import get_db
from src.admin.dependencies import require_admin
from src.admin.services.ip_block_service import IPBlockService

router = APIRouter(prefix="/admin/ip-blocks", tags=["admin"])


@router.get("/")
async def list_blocks(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    svc = IPBlockService(db)
    return {"blocks": await svc.list_active()}


@router.post("/")
async def block_ip(body: dict, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    svc = IPBlockService(db)
    ip = body.get("ip_address", "")
    reason = body.get("reason", "")
    hours = body.get("hours", 24)
    if body.get("permanent"):
        return await svc.block_permanent(ip, reason)
    return await svc.block(ip, reason, hours)


@router.post("/{block_id}/unblock")
async def unblock_ip(block_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    svc = IPBlockService(db)
    if not await svc.unblock(block_id):
        raise HTTPException(status_code=404, detail="Block not found")
    return {"message": "IP unblocked"}
