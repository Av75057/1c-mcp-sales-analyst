from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.models import Session as SessionModel
from src.admin.models import User
from src.auth.service import AuthService


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, username: str, password: str, role: str, email: str | None = None) -> User:
        user = User(username=username, password_hash=AuthService.hash_password(password), role=role, email=email)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, **kwargs: Any) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for k, v in kwargs.items():
            if k == "password":
                user.password_hash = AuthService.hash_password(v)
            elif hasattr(user, k):
                setattr(user, k, v)
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        await self.db.delete(user)
        await self.db.commit()
        return True

    async def block(self, user_id: int, minutes: int = 30) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def unblock(self, user_id: int) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.locked_until = None
        user.failed_login_attempts = 0
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def reset_sessions(self, user_id: int) -> int:
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.user_id == user_id, SessionModel.is_active == True)
        )
        sessions = list(result.scalars().all())
        for s in sessions:
            s.is_active = False
        await self.db.commit()
        return len(sessions)
