from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.cache import CachedC1Client
from src.admin.multitenant.client_factory import ClientFactory
from src.logger import logger


class ConnectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        conn_id = request.headers.get("X-Connection-ID")
        org_id = request.headers.get("X-Org-ID")
        if conn_id:
            try:
                from src.clients.connection_aware import current_connection_id
                client = await ClientFactory.get_c1(connection_id=conn_id)
                if org_id:
                    client.set_org(org_id)
                cached = CachedC1Client(client, ttl=30)
                from src.tools import set_connection_client
                set_connection_client(cached, conn_id)
                current_connection_id.set(conn_id)
                logger.info("[Connection] Switched to: {} (id={}) org={}", client.base_url, conn_id, org_id or "-")
            except Exception as e:
                logger.warning("[Connection] Failed: {}", e)

        return await call_next(request)
