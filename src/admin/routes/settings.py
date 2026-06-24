from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.database import get_db
from src.admin.dependencies import require_admin
from src.admin.services.settings_service import SettingsService

router = APIRouter(prefix="/admin/settings", tags=["admin"])


@router.get("/")
async def list_settings(
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = SettingsService(db)
    return {"settings": await svc.get_all(category=category), "categories": await svc.get_categories()}


@router.get("/{key}")
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = SettingsService(db)
    s = await svc.get(key)
    if not s:
        raise HTTPException(status_code=404, detail="Setting not found")
    return s


@router.put("/{key}")
async def update_setting(
    key: str,
    body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    svc = SettingsService(db)
    result = await svc.set(
        key=key,
        value=body.get("value", ""),
        description=body.get("description"),
        category=body.get("category", "general"),
        changed_by=admin.id,
        is_secret=body.get("is_secret", False),
    )
    return result


@router.get("/{key}/history")
async def get_setting_history(
    key: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = SettingsService(db)
    return {"history": await svc.get_history(key)}


@router.post("/{key}/rollback/{history_id}")
async def rollback_setting(
    key: str,
    history_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    svc = SettingsService(db)
    result = await svc.rollback(history_id, changed_by=admin.id)
    if not result:
        raise HTTPException(status_code=404, detail="History entry not found")
    return result


@router.post("/seed")
async def seed_settings(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = SettingsService(db)
    await svc.seed_defaults()
    return {"message": "Default settings created"}
