from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.database import get_db
from src.admin.dependencies import require_admin
from src.admin.models import User
from src.admin.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.get("/")
async def list_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = UserService(db)
    users = await svc.list_all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "locked_until": u.locked_until.isoformat() if u.locked_until else None,
        }
        for u in users
    ]


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "locked_until": user.locked_until.isoformat() if user.locked_until else None,
    }


@router.post("/")
async def create_user(
    body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    svc = UserService(db)
    if await svc.get_by_username(body["username"]):
        raise HTTPException(status_code=409, detail="Username already exists")
    user = await svc.create(
        username=body["username"],
        password=body["password"],
        role=body.get("role", "viewer"),
        email=body.get("email"),
    )
    return {"id": user.id, "username": user.username, "role": user.role}


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = UserService(db)
    user = await svc.update(user_id, **{k: v for k, v in body.items() if k in ("username", "email", "role", "is_active", "password") and v is not None})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "role": user.role}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    svc = UserService(db)
    ok = await svc.delete(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


@router.post("/{user_id}/block")
async def block_user(
    user_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = UserService(db)
    user = await svc.block(user_id, minutes=body.get("minutes", 30))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User blocked until {user.locked_until}"}


@router.post("/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = UserService(db)
    await svc.unblock(user_id)
    return {"message": "User unblocked"}


@router.post("/{user_id}/reset-sessions")
async def reset_sessions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    svc = UserService(db)
    count = await svc.reset_sessions(user_id)
    return {"message": f"{count} sessions terminated"}
