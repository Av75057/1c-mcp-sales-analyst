from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.database import get_db
from src.admin.dependencies import require_admin
from src.admin.models import User
from src.admin.services.api_key_service import APIKeyService

router = APIRouter(prefix="/admin/api-keys", tags=["admin"])


@router.get("/")
async def list_keys(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    svc = APIKeyService(db)
    return {"keys": await svc.list_all()}


@router.post("/")
async def create_key(body: dict, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    svc = APIKeyService(db)
    plain_key, info = await svc.create(name=body.get("name", "default"), user_id=body.get("user_id", 1), expires_days=body.get("expires_days"))
    return {"plain_key": plain_key, "info": info, "warning": "Save this key now — it won't be shown again"}


@router.post("/{key_id}/revoke")
async def revoke_key(key_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    svc = APIKeyService(db)
    if not await svc.revoke(key_id):
        raise HTTPException(status_code=404, detail="Key not found")
    return {"message": "Key revoked"}
