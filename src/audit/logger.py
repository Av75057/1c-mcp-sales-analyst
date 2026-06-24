from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class AuditEventType(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    ACCESS_DENIED = "access_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    MCP_TOOL_CALL = "mcp_tool_call"


class AuditEvent(BaseModel):
    timestamp: str
    event_type: AuditEventType
    username: str | None = None
    ip_address: str = ""
    user_agent: str = ""
    resource: str = ""
    method: str = ""
    status_code: int | None = None
    details: dict[str, Any] | None = None
    duration_ms: int | None = None


class SensitiveDataFilter(logging.Filter):
    PATTERNS = [
        (re.compile(r"password['\"]?\s*[:=]\s*['\"]?([^'\"}\s]+)", re.I), r"password='***'"),
        (re.compile(r"token['\"]?\s*[:=]\s*['\"]?([^'\"}\s]+)", re.I), r"token='***'"),
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "***@***.***"),
        (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "****-****-****-****"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


class AuditLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger("audit")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        handler = logging.FileHandler(str(self.log_dir / "audit.log"), encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)
        self._logger.addFilter(SensitiveDataFilter())

    async def _log(self, event: AuditEvent) -> None:
        self._logger.info(event.model_dump_json())

    async def log_login(self, username: str, success: bool, ip: str = "", user_agent: str = "") -> None:
        await self._log(AuditEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILED,
            username=username,
            ip_address=ip,
            user_agent=user_agent,
            resource="/api/auth/login",
            method="POST",
            status_code=200 if success else 401,
        ))

    async def log_access_denied(self, username: str, resource: str, role: str) -> None:
        await self._log(AuditEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_type=AuditEventType.ACCESS_DENIED,
            username=username,
            resource=resource,
            details={"role": role},
            status_code=403,
        ))

    async def log_rate_limit_exceeded(self, ip: str, resource: str) -> None:
        await self._log(AuditEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip,
            resource=resource,
        ))

    async def log_data_access(self, username: str, resource: str, method: str, status: int, duration_ms: int = 0) -> None:
        await self._log(AuditEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_type=AuditEventType.DATA_ACCESS,
            username=username,
            resource=resource,
            method=method,
            status_code=status,
            duration_ms=duration_ms,
        ))


audit_logger = AuditLogger()
