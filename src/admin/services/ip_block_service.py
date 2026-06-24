from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.models import IPBlock


class IPBlockService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_active(self) -> list[dict[str, Any]]:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(IPBlock).where((IPBlock.expires_at > now) | (IPBlock.is_permanent == True)).order_by(IPBlock.blocked_at.desc())
        )
        return [
            {
                "id": b.id,
                "ip_address": b.ip_address,
                "reason": b.reason,
                "blocked_at": b.blocked_at.isoformat() if b.blocked_at else None,
                "expires_at": b.expires_at.isoformat() if b.expires_at else None,
                "is_permanent": b.is_permanent,
            }
            for b in result.scalars().all()
        ]

    async def block(self, ip_address: str, reason: str = "", hours: int = 24) -> dict[str, Any]:
        block = IPBlock(ip_address=ip_address, reason=reason, expires_at=datetime.utcnow() + timedelta(hours=hours))
        self.db.add(block)
        await self.db.commit()
        await self.db.refresh(block)
        return {"id": block.id, "ip_address": ip_address, "expires_at": block.expires_at.isoformat() if block.expires_at else None}

    async def block_permanent(self, ip_address: str, reason: str = "") -> dict[str, Any]:
        block = IPBlock(ip_address=ip_address, reason=reason, is_permanent=True)
        self.db.add(block)
        await self.db.commit()
        await self.db.refresh(block)
        return {"id": block.id, "ip_address": ip_address, "is_permanent": True}

    async def unblock(self, block_id: int) -> bool:
        result = await self.db.execute(select(IPBlock).where(IPBlock.id == block_id))
        block = result.scalar_one_or_none()
        if not block:
            return False
        block.expires_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def is_blocked(self, ip_address: str) -> bool:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(IPBlock).where(
                IPBlock.ip_address == ip_address,
                (IPBlock.expires_at > now) | (IPBlock.is_permanent == True),
            )
        )
        return result.scalar_one_or_none() is not None
