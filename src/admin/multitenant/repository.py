from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Tenant, OnecConnection, PlatformUser, TenantUser, AdminAuditLog,
)
from .encryption import encryptor


class TenantRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tenant(self, name: str, slug: str) -> Tenant:
        t = Tenant(id=str(uuid.uuid4()), name=name, slug=slug)
        self.db.add(t)
        await self.db.commit()
        await self.db.refresh(t)
        return t

    async def list_tenants(self) -> list[dict]:
        r = await self.db.execute(select(Tenant).order_by(Tenant.name))
        return [_t2d(row) for row in r.scalars()]

    async def get_tenant(self, tenant_id: str) -> dict | None:
        r = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        t = r.scalar_one_or_none()
        return _t2d(t) if t else None

    async def update_tenant(self, tenant_id: str, **kw) -> bool:
        kw["updated_at"] = datetime.now(timezone.utc)
        r = await self.db.execute(update(Tenant).where(Tenant.id == tenant_id).values(**kw))
        await self.db.commit()
        return r.rowcount > 0

    # --- Connections ---

    async def create_connection(self, tenant_id: str, name: str, base_url: str, username: str, password: str, is_default: bool = False, timeout: int = 30) -> OnecConnection:
        c = OnecConnection(
            id=str(uuid.uuid4()), tenant_id=tenant_id, name=name,
            base_url=base_url, username=username,
            password_encrypted=encryptor.encrypt(password),
            is_default=is_default, timeout_seconds=timeout,
        )
        self.db.add(c)
        await self.db.commit()
        await self.db.refresh(c)
        return c

    async def list_connections(self, tenant_id: str) -> list[dict]:
        r = await self.db.execute(select(OnecConnection).where(OnecConnection.tenant_id == tenant_id).order_by(OnecConnection.name))
        return [_c2d(row) for row in r.scalars()]

    async def get_connection(self, connection_id: str) -> dict | None:
        r = await self.db.execute(select(OnecConnection).where(OnecConnection.id == connection_id))
        c = r.scalar_one_or_none()
        return _c2d(c) if c else None

    async def update_connection(self, connection_id: str, **kw) -> bool:
        kw["updated_at"] = datetime.now(timezone.utc)
        if "password" in kw:
            kw["password_encrypted"] = encryptor.encrypt(kw.pop("password"))
        r = await self.db.execute(update(OnecConnection).where(OnecConnection.id == connection_id).values(**kw))
        await self.db.commit()
        return r.rowcount > 0

    async def delete_connection(self, connection_id: str) -> bool:
        r = await self.db.execute(delete(OnecConnection).where(OnecConnection.id == connection_id))
        await self.db.commit()
        return r.rowcount > 0

    async def set_health(self, connection_id: str, status: str, error: str = ""):
        await self.db.execute(
            update(OnecConnection).where(OnecConnection.id == connection_id).values(
                health_status=status, last_health_check=datetime.now(timezone.utc),
                last_error=error or None,
            )
        )
        await self.db.commit()

    # --- Users ---

    async def create_user(self, email: str, password_hash: str, full_name: str = "", is_superadmin: bool = False) -> PlatformUser:
        u = PlatformUser(id=str(uuid.uuid4()), email=email, password_hash=password_hash, full_name=full_name, is_superadmin=is_superadmin)
        self.db.add(u)
        await self.db.commit()
        await self.db.refresh(u)
        return u

    async def list_users(self) -> list[dict]:
        r = await self.db.execute(select(PlatformUser).order_by(PlatformUser.email))
        return [_u2d(row) for row in r.scalars()]

    async def get_user(self, user_id: str) -> dict | None:
        r = await self.db.execute(select(PlatformUser).where(PlatformUser.id == user_id))
        u = r.scalar_one_or_none()
        return _u2d(u) if u else None

    async def get_user_by_email(self, email: str) -> PlatformUser | None:
        r = await self.db.execute(select(PlatformUser).where(PlatformUser.email == email))
        return r.scalar_one_or_none()

    async def update_user(self, user_id: str, **kw) -> bool:
        kw["updated_at"] = datetime.now(timezone.utc)
        r = await self.db.execute(update(PlatformUser).where(PlatformUser.id == user_id).values(**kw))
        await self.db.commit()
        return r.rowcount > 0

    # --- Tenant-User ---

    async def add_tenant_user(self, tenant_id: str, user_id: str, role: str = "viewer", allowed_connections: list[str] | None = None) -> TenantUser:
        tu = TenantUser(id=str(uuid.uuid4()), tenant_id=tenant_id, user_id=user_id, role=role, allowed_connection_ids=allowed_connections)
        self.db.add(tu)
        await self.db.commit()
        return tu

    async def get_user_tenants(self, user_id: str) -> list[dict]:
        r = await self.db.execute(
            select(TenantUser, Tenant).join(Tenant, TenantUser.tenant_id == Tenant.id).where(TenantUser.user_id == user_id)
        )
        result = []
        for tu, t in r:
            result.append({"tenant_id": t.id, "tenant_name": t.name, "role": tu.role, "slug": t.slug, "allowed_connections": tu.allowed_connection_ids})
        return result

    # --- Audit ---

    async def log(self, actor_user_id: str, action: str, resource_type: str = "", resource_id: str = "", details: dict | None = None, tenant_id: str = "", ip: str = ""):
        entry = AdminAuditLog(
            id=str(uuid.uuid4()), actor_user_id=actor_user_id, action=action,
            resource_type=resource_type, resource_id=resource_id,
            details=details, tenant_id=tenant_id or None, ip_address=ip,
        )
        self.db.add(entry)
        await self.db.commit()

    async def list_audit(self, limit: int = 50) -> list[dict]:
        r = await self.db.execute(select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(limit))
        return [_a2d(row) for row in r.scalars()]


def _t2d(t: Tenant) -> dict:
    return {"id": t.id, "name": t.name, "slug": t.slug, "is_active": t.is_active, "created_at": str(t.created_at) if t.created_at else ""}


def _c2d(c: OnecConnection) -> dict:
    return {"id": c.id, "tenant_id": c.tenant_id, "name": c.name, "config_type": c.config_type,
            "base_url": c.base_url, "username": c.username, "password_encrypted": c.password_encrypted,
            "is_default": c.is_default, "timeout_seconds": c.timeout_seconds,
            "health_status": c.health_status, "last_health_check": str(c.last_health_check) if c.last_health_check else "",
            "last_error": c.last_error, "created_at": str(c.created_at) if c.created_at else ""}


def _u2d(u: PlatformUser) -> dict:
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "is_superadmin": u.is_superadmin,
            "is_active": u.is_active, "last_login_at": str(u.last_login_at) if u.last_login_at else "",
            "created_at": str(u.created_at) if u.created_at else ""}


def _a2d(a: AdminAuditLog) -> dict:
    return {"id": a.id, "actor_user_id": a.actor_user_id, "action": a.action,
            "resource_type": a.resource_type, "resource_id": a.resource_id,
            "details": a.details, "tenant_id": a.tenant_id,
            "ip_address": a.ip_address, "created_at": str(a.created_at) if a.created_at else ""}
