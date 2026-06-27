from __future__ import annotations

import time
from typing import Any

from src.logger import logger

METADATA_CACHE: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 3600


class MetadataService:
    def __init__(self) -> None:
        self._cache = METADATA_CACHE

    async def get_config(self) -> dict[str, Any]:
        if cached := self._cache.get("config"):
            if time.time() - cached[0] < CACHE_TTL:
                return cached[1]
        config = {"name": "1С:УНФ", "configuration": "УНФ", "version": "1.0", "mode": "production", "server": "1c.company.ru"}
        self._cache["config"] = (time.time(), config)
        return config

    async def describe(self, object_type: str | None = None, search: str | None = None) -> list[dict[str, Any]]:
        objects = [
            {"name": "Номенклатура", "type": "Catalog", "fields_count": 25, "description": "Товары и услуги"},
            {"name": "Контрагенты", "type": "Catalog", "fields_count": 30, "description": "Контрагенты"},
            {"name": "Продажи", "type": "Register", "fields_count": 15, "description": "Продажи"},
            {"name": "Закупки", "type": "Register", "fields_count": 15, "description": "Закупки"},
            {"name": "Остатки", "type": "Register", "fields_count": 10, "description": "Остатки"},
        ]
        if object_type:
            objects = [o for o in objects if o["type"].lower() == object_type.lower()]
        if search:
            try:
                from rapidfuzz import fuzz
                objects = [o for o in objects if fuzz.partial_ratio(search.lower(), o["name"].lower()) > 60]
            except ImportError:
                objects = [o for o in objects if search.lower() in o["name"].lower()]
        return objects

    async def get_structure(self, object_name: str) -> dict[str, Any]:
        cache_key = f"structure_{object_name}"
        if cached := self._cache.get(cache_key):
            if time.time() - cached[0] < CACHE_TTL:
                return cached[1]
        structure = {"name": object_name, "type": "Catalog", "fields": [{"name": "Наименование", "type": "String"}, {"name": "Код", "type": "String"}]}
        self._cache[cache_key] = (time.time(), structure)
        return structure

    async def invalidate_cache(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count


metadata_service = MetadataService()
