"""FastAPI зависимости для проверки прав доступа к дашбордам."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from src.dashboard.rbac.service import rbac_service


async def require_dashboard_access(request: Request, dashboard_id: str, permission: str = "view") -> str:
    """Проверяет, имеет ли пользователь доступ к дашборду.

    Возвращает ID пользователя (или 'anonymous').
    """
    payload = getattr(request.state, "user", None)
    user_id = payload.sub if payload else "anonymous"

    if not rbac_service.can_access(dashboard_id, user_id, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Нет прав на {permission} дашборда {dashboard_id}",
        )
    return user_id
