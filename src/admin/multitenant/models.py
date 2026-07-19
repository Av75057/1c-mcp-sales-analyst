from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import select, update, delete

MultiBase = declarative_base()


def _now():
    return datetime.now(timezone.utc)


def _new_id():
    return str(uuid.uuid4())


class Tenant(MultiBase):
    __tablename__ = "tenants"
    id = Column(String(36), primary_key=True, default=_new_id)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class OnecConnection(MultiBase):
    __tablename__ = "onec_connections"
    id = Column(String(36), primary_key=True, default=_new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    config_type = Column(String(50), nullable=False, default="http")
    base_url = Column(String(500))
    username = Column(String(200))
    password_encrypted = Column(Text)
    is_default = Column(Boolean, default=False)
    timeout_seconds = Column(Integer, default=30)
    max_concurrent_requests = Column(Integer, default=10)
    last_health_check = Column(DateTime, nullable=True)
    health_status = Column(String(20), default="unknown")
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class PlatformUser(MultiBase):
    __tablename__ = "platform_users"
    id = Column(String(36), primary_key=True, default=_new_id)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    is_superadmin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class TenantUser(MultiBase):
    __tablename__ = "tenant_users"
    id = Column(String(36), primary_key=True, default=_new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("platform_users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="viewer")
    allowed_connection_ids = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_now)
    __table_args__ = ({"sqlite_autoincrement": False},)


class AdminAuditLog(MultiBase):
    __tablename__ = "admin_audit_log"
    id = Column(String(36), primary_key=True, default=_new_id)
    actor_user_id = Column(String(36), ForeignKey("platform_users.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(36))
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=_now)


async def init_multitenant_db(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(MultiBase.metadata.create_all)
