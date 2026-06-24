from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.models import Setting, SettingsHistory


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, category: str | None = None) -> list[dict[str, Any]]:
        q = select(Setting)
        if category:
            q = q.where(Setting.category == category)
        q = q.order_by(Setting.category, Setting.key)
        result = await self.db.execute(q)
        return [
            {
                "id": s.id,
                "key": s.key,
                "value": "***" if s.is_secret else s.value,
                "description": s.description,
                "category": s.category,
                "is_secret": s.is_secret,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in result.scalars().all()
        ]

    async def get(self, key: str) -> dict[str, Any] | None:
        result = await self.db.execute(select(Setting).where(Setting.key == key))
        s = result.scalar_one_or_none()
        if not s:
            return None
        return {
            "id": s.id,
            "key": s.key,
            "value": "***" if s.is_secret else s.value,
            "description": s.description,
            "category": s.category,
            "is_secret": s.is_secret,
        }

    async def set(
        self,
        key: str,
        value: str,
        description: str | None = None,
        category: str = "general",
        changed_by: int | None = None,
        is_secret: bool = False,
    ) -> dict[str, Any]:
        result = await self.db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()

        if setting:
            old_val = setting.value
            if old_val != value:
                history = SettingsHistory(setting_id=setting.id, old_value=old_val, new_value=value, changed_by=changed_by)
                self.db.add(history)
            setting.value = value
            if description:
                setting.description = description
            setting.updated_by = changed_by
            setting.is_secret = is_secret
        else:
            setting = Setting(key=key, value=value, description=description, category=category, updated_by=changed_by, is_secret=is_secret)
            self.db.add(setting)

        await self.db.commit()
        await self.db.refresh(setting)
        return {"id": setting.id, "key": setting.key, "value": "***" if is_secret else value, "category": setting.category}

    async def get_history(self, key: str, limit: int = 50) -> list[dict[str, Any]]:
        result = await self.db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        if not setting:
            return []

        q = (
            select(SettingsHistory)
            .where(SettingsHistory.setting_id == setting.id)
            .order_by(SettingsHistory.changed_at.desc())
            .limit(limit)
        )
        history = await self.db.execute(q)
        return [
            {
                "id": h.id,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "changed_by": h.changed_by,
                "changed_at": h.changed_at.isoformat() if h.changed_at else None,
            }
            for h in history.scalars().all()
        ]

    async def rollback(self, history_id: int, changed_by: int | None = None) -> dict[str, Any] | None:
        result = await self.db.execute(select(SettingsHistory).where(SettingsHistory.id == history_id))
        history = result.scalar_one_or_none()
        if not history:
            return None

        result = await self.db.execute(select(Setting).where(Setting.id == history.setting_id))
        setting = result.scalar_one_or_none()
        if not setting:
            return None

        new_history = SettingsHistory(setting_id=setting.id, old_value=setting.value, new_value=history.old_value, changed_by=changed_by)
        self.db.add(new_history)

        setting.value = history.old_value
        setting.updated_by = changed_by
        await self.db.commit()
        await self.db.refresh(setting)
        return {"id": setting.id, "key": setting.key, "value": setting.value}

    async def get_categories(self) -> list[str]:
        result = await self.db.execute(select(Setting.category).distinct().order_by(Setting.category))
        return [r[0] for r in result.all()]

    async def seed_defaults(self) -> None:
        defaults = [
            ("CACHE_TTL_SECONDS", "300", "Время жизни кэша (сек)", "cache"),
            ("CACHE_MAX_SIZE", "1000", "Макс. размер кэша", "cache"),
            ("C1_TIMEOUT_SECONDS", "60", "Таймаут запроса к 1С (сек)", "timeout"),
            ("C1_MAX_RETRIES", "3", "Макс. число retry", "timeout"),
            ("RATE_LIMIT_DEFAULT", "100/minute", "Лимит запросов по умолчанию", "rate_limit"),
            ("RATE_LIMIT_ADMIN", "200/minute", "Лимит для admin", "rate_limit"),
            ("RATE_LIMIT_ANALYST", "100/minute", "Лимит для analyst", "rate_limit"),
            ("RATE_LIMIT_VIEWER", "30/minute", "Лимит для viewer", "rate_limit"),
            ("ALLOWED_ORIGINS", "http://localhost:8000", "Разрешённые CORS origins", "cors"),
            ("LLM_MODEL", "deepseek-chat", "Модель DeepSeek", "ai"),
            ("LLM_TEMPERATURE", "0.1", "Температура LLM", "ai"),
        ]
        for key, value, desc, cat in defaults:
            result = await self.db.execute(select(Setting).where(Setting.key == key))
            if not result.scalar_one_or_none():
                self.db.add(Setting(key=key, value=value, description=desc, category=cat))
        await self.db.commit()
