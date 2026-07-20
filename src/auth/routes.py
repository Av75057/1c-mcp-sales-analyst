from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from passlib.hash import bcrypt

from src.admin.database import get_db
from src.admin.multitenant.repository import TenantRepository
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
    # Try built-in admin auth first
    user = await AuthService.authenticate(db, form_data.username, form_data.password)

    if not user:
        # Try platform user auth
        repo = TenantRepository(db)
        platform_user = await repo.get_user_by_email(form_data.username)
        if platform_user and platform_user.is_active and bcrypt.verify(form_data.password, platform_user.password_hash):
            tenants = await repo.get_user_tenants(platform_user.id)
            token = AuthService.create_access_token(
                platform_user.email,
                Role.ADMIN.value,
                extra={"user_id": platform_user.id, "is_platform": True, "tenants": tenants},
            )
            await audit_logger.log_login(platform_user.email, success=True, ip=request.client.host if request else "", user_agent=request.headers.get("user-agent", "") if request else "")
            token.user = {"username": platform_user.email, "role": "admin", "email": platform_user.email, "full_name": platform_user.full_name or platform_user.email}
            if response:
                is_https = request.url.scheme == "https" if request else False
                response.set_cookie(key="access_token", value=token.access_token, httponly=True, secure=is_https, samesite="lax", max_age=token.expires_in)
            return token

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

    token.user = {"username": user.username, "role": user.role.value, "email": user.username, "full_name": user.username}
    if response:
        is_https = request.url.scheme == "https" if request else False
        response.set_cookie(key="access_token", value=token.access_token, httponly=True, secure=is_https, samesite="lax", max_age=token.expires_in)

    return token


@router.post("/logout")
async def logout(request: Request, response: Response):
    is_https = request.url.scheme == "https" if request else False
    response.delete_cookie("access_token", secure=is_https)
    return {"message": "Logged out"}


@router.get("/me")
async def me(payload=Depends(get_token_payload), db: AsyncSession = Depends(get_db)):
    username = payload.sub
    role = payload.role
    email = username
    full_name = username

    # Try platform user first
    from src.admin.multitenant.repository import TenantRepository
    repo = TenantRepository(db)
    pu = await repo.get_user_by_email(username)
    if pu:
        full_name = pu.full_name or pu.email
        email = pu.email

    return {"username": username, "role": role, "email": email, "full_name": full_name}
