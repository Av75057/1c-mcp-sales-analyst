from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.admin.database import get_db
from src.admin.models import User
from src.auth.dependencies import get_token_payload
from src.auth.models import Role


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload=Depends(get_token_payload),
) -> User:
    result = await db.execute(select(User).where(User.username == payload.sub))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
