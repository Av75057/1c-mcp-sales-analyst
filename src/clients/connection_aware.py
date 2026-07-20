from __future__ import annotations

from contextvars import ContextVar

# Context variable for the active connection ID (set by middleware or route handler)
current_connection_id: ContextVar[str | None] = ContextVar("current_connection_id", default=None)


async def resolve_client():
    """Return a C1Client for the current connection context.
    
    If current_connection_id is set, uses the connection's credentials from the DB.
    Otherwise falls back to the global C1Client from settings.
    """
    conn_id = current_connection_id.get()
    if not conn_id:
        from src.tools import get_client as _global_client
        return _global_client()

    from src.admin.multitenant.client_factory import ClientFactory
    from src.admin.multitenant.repository import TenantRepository
    from src.admin.database import async_session

    try:
        async with async_session() as db:
            repo = TenantRepository(db)
            conn_data = await repo.get_connection(conn_id)
            if conn_data:
                return await ClientFactory.get_c1(connection_id=conn_id, db=None)
    except Exception:
        pass
    
    from src.tools import get_client as _global_client
    return _global_client()
