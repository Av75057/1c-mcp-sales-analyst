from __future__ import annotations

import inspect
from datetime import datetime, timedelta
from typing import Any

from src.mcp.tools import TOOLS_REGISTRY
from src.admin.services.audit_service import AuditService


class ToolsService:
    def get_all(self) -> list[dict[str, Any]]:
        tools = []
        for name, func in TOOLS_REGISTRY.items():
            sig = inspect.signature(func)
            params = []
            for pname, p in sig.parameters.items():
                if pname in ("self", "request", "kwargs"):
                    continue
                params.append({
                    "name": pname,
                    "default": None if p.default is inspect.Parameter.empty else str(p.default),
                    "required": p.default is inspect.Parameter.empty,
                })
            tools.append({
                "name": name,
                "doc": (func.__doc__ or "").strip()[:200],
                "parameters": params,
            })
        return tools

    def get_statistics(self, hours: int = 24) -> dict[str, Any]:
        audit = AuditService()
        logs = audit.get_logs(event_type="data_access", limit=10000)
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        stats: dict[str, Any] = {}
        for log in logs:
            ts = log.get("timestamp", "")
            if ts < cutoff:
                continue
            resource = log.get("resource", "")
            if not resource.startswith("/api/"):
                continue
            name = resource.split("/")[-1]
            if name not in stats:
                stats[name] = {"call_count": 0, "error_count": 0}
            stats[name]["call_count"] += 1
            if log.get("status_code", 200) >= 400:
                stats[name]["error_count"] += 1
        return stats

    def get_recent_calls(self, limit: int = 50) -> list[dict[str, Any]]:
        audit = AuditService()
        logs = audit.get_logs(event_type="data_access", limit=limit)
        return [
            {
                "timestamp": l.get("timestamp", ""),
                "username": l.get("username", ""),
                "resource": l.get("resource", ""),
                "method": l.get("method", ""),
                "status_code": l.get("status_code", ""),
                "duration_ms": l.get("duration_ms"),
            }
            for l in logs
        ]
