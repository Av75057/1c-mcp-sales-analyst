from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class AuditService:
    def __init__(self):
        self.log_path = Path(__file__).resolve().parent.parent.parent.parent / "logs" / "audit.log"

    def _read_logs(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        try:
            lines = self.log_path.read_text(encoding="utf-8").strip().split("\n")
            result = []
            for line in lines:
                if line.strip():
                    try:
                        result.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return result
        except Exception:
            return []

    def get_logs(
        self,
        username: str | None = None,
        event_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        ip_address: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        logs = self._read_logs()
        filtered = []
        for log in logs:
            if username and log.get("username") != username:
                continue
            if event_type and log.get("event_type") != event_type:
                continue
            if ip_address and log.get("ip_address") != ip_address:
                continue
            if date_from:
                ts = log.get("timestamp", "")
                if ts < date_from:
                    continue
            if date_to:
                ts = log.get("timestamp", "")
                if ts > date_to:
                    continue
            filtered.append(log)
            if len(filtered) >= limit:
                break
        return filtered

    def get_statistics(self, hours: int = 24) -> dict[str, Any]:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        logs = self.get_logs(limit=10000)

        stats: dict[str, Any] = {
            "total": 0, "login_success": 0, "login_failed": 0,
            "access_denied": 0, "rate_limit_exceeded": 0,
            "users": set(), "ips": set(),
        }
        for log in logs:
            ts = log.get("timestamp", "")
            if ts < cutoff:
                continue
            stats["total"] += 1
            et = log.get("event_type", "")
            if et == "login_success":
                stats["login_success"] += 1
            elif et == "login_failed":
                stats["login_failed"] += 1
            elif et == "access_denied":
                stats["access_denied"] += 1
            elif et == "rate_limit_exceeded":
                stats["rate_limit_exceeded"] += 1
            if log.get("username"):
                stats["users"].add(log["username"])
            if log.get("ip_address"):
                stats["ips"].add(log["ip_address"])

        stats["unique_users"] = len(stats.pop("users"))
        stats["unique_ips"] = len(stats.pop("ips"))
        return stats

    def export_csv(self, logs: list[dict[str, Any]]) -> str:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "event_type", "username", "ip_address", "resource", "status_code"])
        for log in logs:
            writer.writerow([
                log.get("timestamp", ""),
                log.get("event_type", ""),
                log.get("username", ""),
                log.get("ip_address", ""),
                log.get("resource", ""),
                log.get("status_code", ""),
            ])
        return output.getvalue()
