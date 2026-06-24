from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.models import APIKey


class APIKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[dict[str, Any]]:
        result = await self.db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
        return [
            {
                "id": k.id,
                "name": k.name,
                "user_id": k.user_id,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "last_used": k.last_used.isoformat() if k.last_used else None,
            }
            for k in result.scalars().all()
        ]

    async def create(self, name: str, user_id: int, expires_days: int | None = None) -> tuple[str, dict[str, Any]]:
        plain_key = secrets.token_urlsafe(32)
        key_hash = sha256(plain_key.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=expires_days) if expires_days else None

        api_key = APIKey(key_hash=key_hash, name=name, user_id=user_id, expires_at=expires_at)
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)

        return plain_key, {"id": api_key.id, "name": api_key.name, "created_at": api_key.created_at.isoformat() if api_key.created_at else None}

    async def revoke(self, key_id: int) -> bool:
        result = await self.db.execute(select(APIKey).where(APIKey.id == key_id))
        k = result.scalar_one_or_none()
        if not k:
            return False
        k.is_active = False
        await self.db.commit()
        return True

    async def validate(self, plain_key: str) -> tuple[bool, APIKey | None]:
        key_hash = sha256(plain_key.encode()).hexdigest()
        result = await self.db.execute(select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True))
        k = result.scalar_one_or_none()
        if not k:
            return False, None
        if k.expires_at and k.expires_at < datetime.utcnow():
            return False, None
        k.last_used = datetime.utcnow()
        await self.db.commit()
        return True, k
