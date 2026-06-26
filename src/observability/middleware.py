from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, Request, Response

from src.observability.metrics import http_requests_total, http_request_duration_seconds

SKIP_PATHS = {"/metrics", "/health", "/health/live", "/health/ready"}


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start = time.perf_counter()

        response: Response = await call_next(request)
        elapsed = time.perf_counter() - start
        endpoint = request.url.path
        method = request.method

        http_requests_total.labels(method=method, endpoint=endpoint, status_code=response.status_code).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(elapsed)

        response.headers["X-Request-ID"] = request_id
        return response
