from __future__ import annotations

import asyncio
import shutil
import time
from typing import Any

import psutil

from src.config import settings
from src.logger import logger
from src.resilience.circuit_breaker import c1_cb, deepseek_cb


async def check_database() -> dict[str, Any]:
    start = time.time()
    try:
        from src.admin.database import async_session
        from sqlalchemy import text
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency, 2)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def check_c1() -> dict[str, Any]:
    start = time.time()
    try:
        from src.clients.c1_client import C1Client
        c1 = C1Client()
        try:
            await asyncio.wait_for(c1.get_stock(warehouse=None, nomenclature=None, min_quantity=1), timeout=5.0)
            latency = (time.time() - start) * 1000
            cb_state = c1_cb.state.value
            return {"status": "degraded" if cb_state == "open" else "ok", "latency_ms": round(latency, 2), "details": {"endpoint": settings.c1_base_url, "circuit_breaker": cb_state}}
        finally:
            await c1.close()
    except asyncio.TimeoutError:
        return {"status": "error", "error": "timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_deepseek() -> dict[str, Any]:
    cb_state = deepseek_cb.state.value
    api_key_ok = bool(settings.deepseek_api_key)
    if not api_key_ok:
        return {"status": "error", "error": "api_key_not_configured"}
    return {"status": "degraded" if cb_state == "open" else "ok", "details": {"api_key_configured": True, "model": settings.llm_model, "circuit_breaker": cb_state}}


def check_disk() -> dict[str, Any]:
    disk = shutil.disk_usage("/")
    free_gb = disk.free / (1024**3)
    total_gb = disk.total / (1024**3)
    used_pct = (disk.total - disk.free) / disk.total * 100
    status = "ok" if free_gb > 5 else "degraded" if free_gb > 1 else "error"
    return {"status": status, "details": {"free_gb": round(free_gb, 1), "total_gb": round(total_gb, 1), "percent_used": round(used_pct, 1)}}


def check_memory() -> dict[str, Any]:
    mem = psutil.virtual_memory()
    used_mb = mem.used / (1024**2)
    total_mb = mem.total / (1024**2)
    pct = mem.percent
    status = "ok" if pct < 80 else "degraded" if pct < 95 else "error"
    return {"status": status, "details": {"used_mb": round(used_mb, 1), "total_mb": round(total_mb, 1), "percent_used": pct}}


def check_circuit_breakers() -> dict[str, Any]:
    return {
        "status": "ok",
        "details": {
            "deepseek": deepseek_cb.state.value,
            "c1": c1_cb.state.value,
        },
    }


async def all_checks() -> dict[str, Any]:
    results = await asyncio.gather(check_database(), check_c1(), return_exceptions=True)
    db_result = results[0] if not isinstance(results[0], Exception) else {"status": "error", "error": str(results[0])}
    c1_result = results[1] if not isinstance(results[1], Exception) else {"status": "error", "error": str(results[1])}

    checks = {
        "database": db_result,
        "c1": c1_result,
        "deepseek": check_deepseek(),
        "disk": check_disk(),
        "memory": check_memory(),
        "circuit_breakers": check_circuit_breakers(),
    }

    ok_count = sum(1 for c in checks.values() if c["status"] == "ok")
    error_count = sum(1 for c in checks.values() if c["status"] == "error")

    if error_count > 0:
        overall = "unhealthy"
    elif ok_count == len(checks):
        overall = "healthy"
    else:
        overall = "degraded"

    return {"status": overall, "checks": checks}
