from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.cache import CachedC1Client
from src.clients.c1_client import C1Client
from src.clients.connection_aware import current_connection_id
from src.logger import logger


class ConnectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        conn_id = request.headers.get("X-Connection-ID")
        if conn_id:
            try:
                from src.admin.multitenant.encryption import encryptor
                from src.admin.multitenant.repository import TenantRepository
                from src.admin.database import async_session

                async with async_session() as db:
                    repo = TenantRepository(db)
                    conn_data = await repo.get_connection(conn_id)
            if conn_data:
                password = encryptor.decrypt(conn_data.get("password_encrypted", ""))
                client = C1Client()
                client.base_url = conn_data["base_url"].rstrip("/")
                import base64
                raw = f"{conn_data['username']}:{password}".encode("utf-8")
                client._auth_header = "Basic " + base64.b64encode(raw).decode("ascii")
                request.state.connection_id = conn_id
                cached = CachedC1Client(client, ttl=30)
                from src.tools import set_connection_client
                set_connection_client(cached, conn_id)
                logger.info("[Connection] Switched to '{}' ({})", conn_data["name"], conn_data["base_url"])
            except Exception as e:
                logger.warning("[Connection] Failed to setup connection: {}", e)
        
        return await call_next(request)
