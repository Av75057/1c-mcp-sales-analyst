from __future__ import annotations

import hashlib
import re
from typing import Any

from pydantic import BaseModel

from src.logger import logger


class ValidationResult(BaseModel):
    is_valid: bool
    error: str | None = None
    error_line: int | None = None
    error_column: int | None = None
    suggestion: str | None = None
    query_hash: str = ""


class QueryValidationGuardrails:
    FORBIDDEN_OPS = {
        "ИЗМЕНИТЬ", "ИЗМЕНЕНИЕ", "UPDATE", "УДАЛИТЬ", "УДАЛЕНИЕ", "DELETE",
        "ДОБАВИТЬ", "INSERT", "ОБНОВИТЬ", "DROP", "CREATE", "ALTER",
        "TRUNCATE", "EXEC", "EXECUTE",
    }
    FORBIDDEN_PATTERNS = [
        re.compile(r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)", re.IGNORECASE),
        re.compile(r"--"),
        re.compile(r"/\*"),
        re.compile(r"xp_", re.IGNORECASE),
        re.compile(r"\bEXEC\s*\(", re.IGNORECASE),
    ]
    MAX_QUERY_LENGTH = 5000
    MAX_PARAMS_COUNT = 50
    MAX_PARAM_VALUE_LENGTH = 500

    @classmethod
    def validate(cls, query: str, params: dict[str, Any] | None = None) -> ValidationResult:
        qh = hashlib.sha256(query.encode()).hexdigest()[:16]

        if not query or not query.strip():
            return ValidationResult(is_valid=False, error="Запрос пустой", suggestion="Введите текст запроса", query_hash=qh)

        if len(query) > cls.MAX_QUERY_LENGTH:
            return ValidationResult(is_valid=False, error=f"Запрос слишком длинный ({len(query)} сим., макс. {cls.MAX_QUERY_LENGTH})", suggestion="Сократите запрос", query_hash=qh)

        upper = query.upper()

        for op in cls.FORBIDDEN_OPS:
            if re.search(r'\b' + re.escape(op) + r'\b', upper):
                return ValidationResult(is_valid=False, error=f"Запрещённая операция: {op}", suggestion="Разрешены только SELECT/ВЫБРАТЬ", query_hash=qh)

        for pat in cls.FORBIDDEN_PATTERNS:
            if pat.search(query):
                return ValidationResult(is_valid=False, error="Обнаружен опасный паттерн", suggestion="Удалите комментарии и спецсимволы", query_hash=qh)

        if not re.search(r'\bВЫБРАТЬ\b', upper) and not re.search(r'\bSELECT\b', upper):
            return ValidationResult(is_valid=False, error="Запрос должен начинаться с ВЫБРАТЬ/SELECT", suggestion="Добавьте 'ВЫБРАТЬ' в начало", query_hash=qh)

        if params:
            if len(params) > cls.MAX_PARAMS_COUNT:
                return ValidationResult(is_valid=False, error=f"Слишком много параметров ({len(params)}, макс. {cls.MAX_PARAMS_COUNT})", suggestion="Сократите количество параметров", query_hash=qh)
            for k, v in params.items():
                if len(str(v)) > cls.MAX_PARAM_VALUE_LENGTH:
                    return ValidationResult(is_valid=False, error=f"Параметр '{k}' слишком длинный", suggestion=f"Макс. длина: {cls.MAX_PARAM_VALUE_LENGTH}", query_hash=qh)

        return ValidationResult(is_valid=True, query_hash=qh)


class QueryValidator:
    def __init__(self, c1_client: Any = None, cache: Any = None):
        self.c1_client = c1_client
        self.cache = cache

    async def validate(self, query: str, params: dict[str, Any] | None = None, skip_remote: bool = False) -> ValidationResult:
        logger.info("Validating query: {}...", query[:80])

        local = QueryValidationGuardrails.validate(query, params)
        if not local.is_valid:
            return local

        if skip_remote:
            return local

        if self.cache:
            key = f"validate:{local.query_hash}"
            cached = await self.cache.get(key)
            if cached:
                return ValidationResult(**cached)

        try:
            remote = await self._validate_remote(query, params)
            if self.cache and remote.is_valid:
                await self.cache.set(f"validate:{local.query_hash}", remote.model_dump(), ttl=300)
            return remote
        except Exception as e:
            logger.error("Remote validation failed: {}", e)
            return ValidationResult(is_valid=True, error=f"Не удалось проверить в 1С: {e}", suggestion="Запрос будет выполнен с риском ошибки", query_hash=local.query_hash)

    async def _validate_remote(self, query: str, params: dict[str, Any] | None) -> ValidationResult:
        payload = {"query": query, "params": params or {}}
        if hasattr(self.c1_client, "post"):
            response = await self.c1_client.post("/validate_query", json=payload, timeout=10)
            data = response.json() if hasattr(response, "json") else response
        elif hasattr(self.c1_client, "_request"):
            response = await self.c1_client._request("POST", "/validate_query", json=payload)
            data = response.json() if hasattr(response, "json") else response
        else:
            import httpx
            from src.config import settings
            url = f"{settings.c1_base_url}/validate_query"
            async with httpx.AsyncClient(auth=(settings.c1_username, settings.c1_password), timeout=10) as client:
                resp = await client.post(url, json=payload)
                data = resp.json()

        return ValidationResult(
            is_valid=data.get("is_valid", False),
            error=data.get("error"),
            error_line=data.get("error_line"),
            error_column=data.get("error_column"),
            suggestion=data.get("suggestion"),
            query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
        )
