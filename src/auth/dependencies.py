from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from src.auth.models import Role, TokenPayload
from src.auth.service import AuthService


def get_token_payload(request: Request) -> TokenPayload:
    user: TokenPayload | None = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


def require_role(*roles: Role):
    async def _check(user: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
        if user.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not allowed. Required: {[r.value for r in roles]}",
            )
        return user

    return _check
