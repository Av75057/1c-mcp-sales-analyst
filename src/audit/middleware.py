from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, Request, Response

from src.audit.logger import audit_logger

SKIP_PATHS = {"/api/health", "/api/health/performance", "/static", "/docs", "/openapi.json"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in SKIP_PATHS):
            return await call_next(request)

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)

        user = getattr(request.state, "user", None)
        if user and request.method in ("POST", "PUT", "DELETE", "PATCH"):
            await audit_logger.log_data_access(
                username=user.sub,
                resource=path,
                method=request.method,
                status=response.status_code,
                duration_ms=duration_ms,
            )

        return response
