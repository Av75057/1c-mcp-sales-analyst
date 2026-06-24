from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from src.clients.c1_client import C1Client
from src.config import settings
from src.deepseek_client import DeepSeekClient


class HealthService:
    async def check_1c(self) -> dict[str, Any]:
        start = datetime.utcnow()
        try:
            async with C1Client() as client:
                data = await client.get_stock(warehouse=None, nomenclature=None, min_quantity=1)
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                return {"status": "healthy", "response_time_ms": round(elapsed, 0), "items_count": len(data)}
        except Exception as e:
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            return {"status": "unhealthy", "error": str(e), "response_time_ms": round(elapsed, 0)}

    async def check_deepseek(self) -> dict[str, Any]:
        if not settings.deepseek_api_key:
            return {"status": "unhealthy", "error": "API key not configured"}
        start = datetime.utcnow()
        try:
            client = DeepSeekClient()
            ok = await client._call_llm([{"role": "user", "content": "ping"}])
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            return {"status": "healthy", "response_time_ms": round(elapsed, 0), "model": settings.llm_model}
        except Exception as e:
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            return {"status": "unhealthy", "error": str(e), "response_time_ms": round(elapsed, 0)}

    async def check_batch(self) -> dict[str, Any]:
        from src.clients.batch_client import BatchC1Client

        start = datetime.utcnow()
        try:
            async with BatchC1Client() as client:
                result = await client.execute_batch(
                    [{"id": "ping", "method": "GET", "path": "/stock", "params": {"limit": "1"}}],
                    timeout=10,
                )
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                ok = result.get("results", [{}])[0].get("status") == 200
                return {"status": "healthy" if ok else "degraded", "response_time_ms": round(elapsed, 0)}
        except Exception as e:
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            return {"status": "unhealthy", "error": str(e), "response_time_ms": round(elapsed, 0)}

    async def check_all(self) -> dict[str, Any]:
        results = await asyncio.gather(self.check_1c(), self.check_deepseek(), self.check_batch(), return_exceptions=True)

        def safe(idx: int) -> dict[str, Any]:
            r = results[idx]
            if isinstance(r, Exception):
                return {"status": "unhealthy", "error": str(r)}
            return r

        return {"1c": safe(0), "deepseek": safe(1), "batch": safe(2)}
