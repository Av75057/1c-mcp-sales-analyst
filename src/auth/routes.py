from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.database import get_db
from src.audit.logger import audit_logger
from src.auth.dependencies import get_token_payload, require_role
from src.auth.models import Role, User
from src.auth.service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.authenticate(db, form_data.username, form_data.password)
    if not user:
        await audit_logger.log_login(
            form_data.username, success=False,
            ip=request.client.host if request else "",
            user_agent=request.headers.get("user-agent", "") if request else "",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    token = AuthService.create_access_token(user.username, user.role.value)
    await audit_logger.log_login(
        user.username, success=True,
        ip=request.client.host if request else "",
        user_agent=request.headers.get("user-agent", "") if request else "",
    )

    if response:
        response.set_cookie(key="access_token", value=token.access_token, httponly=True, secure=True, samesite="lax", max_age=token.expires_in)

    return token


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me")
async def me(payload=Depends(get_token_payload)):
    return {"username": payload.sub, "role": payload.role}
