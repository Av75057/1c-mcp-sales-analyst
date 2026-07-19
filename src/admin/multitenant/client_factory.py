from __future__ import annotations

from typing import Optional

from src.clients.c1_client import C1Client
from src.clients.batch_client import BatchC1Client
from src.admin.multitenant.encryption import encryptor
from src.admin.multitenant.repository import TenantRepository
from src.admin.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


class ClientFactory:
    """Фабрика клиентов 1С с поддержкой мультитенантности.
    
    По умолчанию использует глобальные настройки из .env.
    При указании connection_id использует данные из таблицы onec_connections.
    """

    _pool: dict[str, C1Client] = {}

    @classmethod
    async def get_c1(
        cls,
        connection_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> C1Client:
        if connection_id:
            key = f"conn_{connection_id}"
            if key not in cls._pool:
                from src.admin.database import async_session
                if db is None:
                    async with async_session() as session:
                        repo = TenantRepository(session)
                        conn_data = await repo.get_connection(connection_id)
                        if not conn_data:
                            raise ValueError(f"Connection {connection_id} not found")
                        password = encryptor.decrypt(conn_data["password_encrypted"])
                        client = C1Client()
                        client.base_url = conn_data["base_url"].rstrip("/")
                        client._auth_header = _make_basic(conn_data["username"], password)
                        cls._pool[key] = client
                else:
                    repo = TenantRepository(db)
                    conn_data = await repo.get_connection(connection_id)
                    if not conn_data:
                        raise ValueError(f"Connection {connection_id} not found")
                    password = encryptor.decrypt(conn_data["password_encrypted"])
                    client = C1Client()
                    client.base_url = conn_data["base_url"].rstrip("/")
                    client._auth_header = _make_basic(conn_data["username"], password)
                    cls._pool[key] = client
            return cls._pool[key]

        from src.tools import get_client
        return get_client()

    @classmethod
    async def get_batch(
        cls,
        connection_id: Optional[str] = None,
    ) -> BatchC1Client:
        if connection_id:
            from src.admin.database import async_session
            async with async_session() as session:
                repo = TenantRepository(session)
                conn_data = await repo.get_connection(connection_id)
                if conn_data:
                    password = encryptor.decrypt(conn_data["password_encrypted"])
                    batch = BatchC1Client()
                    import base64
                    raw = f"{conn_data['username']}:{password}".encode("utf-8")
                    batch._auth_header = "Basic " + base64.b64encode(raw).decode("ascii")
                    batch.base_url = conn_data["base_url"].rstrip("/")
                    return batch

        from src.clients.batch_client import BatchC1Client
        return BatchC1Client()

    @classmethod
    def clear_pool(cls):
        cls._pool.clear()


def _make_basic(username: str, password: str) -> str:
    import base64
    raw = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")
