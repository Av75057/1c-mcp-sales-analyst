from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.service import AuthService
from src.config import settings

PUBLIC_PATHS = [
    "/api/auth/login",
    "/api/auth/logout",
    "/api/health",
    "/api/health/performance",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/static",
    "/login",
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.auth_enabled:
            return await call_next(request)

        path = request.url.path

        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
        else:
            cookie = request.cookies.get("access_token")
            if cookie:
                token = cookie

        if not token:
            accept = request.headers.get("accept", "")
            if "text/html" in accept:
                return RedirectResponse(url="/login")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = AuthService.decode_token(token)
        request.state.user = payload
        return await call_next(request)
