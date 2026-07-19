from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import httpx

from src.admin.database import async_session
from src.admin.multitenant.repository import TenantRepository
from src.admin.multitenant.encryption import encryptor
from src.logger import logger


async def check_connection(conn: dict) -> dict:
    """Проверяет доступность одного подключения к 1С."""
    start = time.time()
    result = {"id": conn["id"], "status": "ok", "latency_ms": 0, "error": ""}
    try:
        password = encryptor.decrypt(conn["password_encrypted"]) if conn.get("password_encrypted") else ""
        import base64
        raw = f"{conn['username']}:{password}".encode("utf-8")
        auth = "Basic " + base64.b64encode(raw).decode("ascii")
        async with httpx.AsyncClient(headers={"Authorization": auth}, timeout=10) as client:
            resp = await client.get(f"{conn['base_url'].rstrip('/')}/stock", params={"limit": "1"})
            result["latency_ms"] = int((time.time() - start) * 1000)
            if resp.status_code >= 500:
                result["status"] = "error"
                result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:200]
    return result


async def run_health_check():
    """Проверяет все подключения и обновляет их статус."""
    try:
        async with async_session() as db:
            repo = TenantRepository(db)
            tenants = await repo.list_tenants()
            all_connections = []
            for t in tenants:
                conns = await repo.list_connections(t["id"])
                all_connections.extend(conns)

            logger.info("[Health] Checking {} connections...", len(all_connections))
            results = await asyncio.gather(*[check_connection(c) for c in all_connections], return_exceptions=True)

            for i, conn in enumerate(all_connections):
                r = results[i]
                if isinstance(r, Exception):
                    await repo.set_health(conn["id"], "error", str(r)[:200])
                else:
                    await repo.set_health(conn["id"], r["status"], r.get("error", ""))
            logger.info("[Health] Check complete: {} ok, {} errors",
                        sum(1 for r in results if isinstance(r, dict) and r["status"] == "ok"),
                        sum(1 for r in results if isinstance(r, dict) and r["status"] == "error"))
    except Exception as e:
        logger.error("[Health] Check failed: {}", e)


async def health_check_loop(interval: int = 300):
    """Фоновый цикл проверки подключений."""
    while True:
        await run_health_check()
        await asyncio.sleep(interval)
