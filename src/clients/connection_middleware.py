from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.cache import CachedC1Client
from src.admin.multitenant.client_factory import ClientFactory
from src.logger import logger


class ConnectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        conn_id = request.headers.get("X-Connection-ID")
        if conn_id:
            try:
                client = await ClientFactory.get_c1(connection_id=conn_id)
                cached = CachedC1Client(client, ttl=30)
                from src.tools import set_connection_client
                set_connection_client(cached, conn_id)
                logger.info("[Connection] Switched to: {}", client.base_url)
            except Exception as e:
                logger.warning("[Connection] Failed: {}", e)

        return await call_next(request)
