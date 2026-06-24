from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.dependencies import get_token_payload, require_role
from src.auth.models import Role, Token, User
from src.auth.service import AuthService
from src.audit.logger import audit_logger

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    response: Response = None,
):
    user = AuthService.authenticate(form_data.username, form_data.password)
    if not user:
        await audit_logger.log_login(
            form_data.username, success=False,
            ip=request.client.host if request else "",
            user_agent=request.headers.get("user-agent", "") if request else "",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = AuthService.create_access_token(user.username, user.role)
    await audit_logger.log_login(
        user.username, success=True,
        ip=request.client.host if request else "",
        user_agent=request.headers.get("user-agent", "") if request else "",
    )

    if response:
        response.set_cookie(
            key="access_token",
            value=token.access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=token.expires_in,
        )

    return token


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me")
async def me(payload=Depends(get_token_payload)):
    user = AuthService.get_user(payload.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.dict_safe()


@router.get("/users")
async def list_users(_=Depends(require_role(Role.ADMIN))):
    return AuthService.list_users()


@router.post("/users")
async def create_user(
    body: dict,
    _=Depends(require_role(Role.ADMIN)),
):
    return AuthService.create_user(
        username=body["username"],
        password=body["password"],
        role=Role(body.get("role", "viewer")),
    ).dict_safe()


@router.patch("/users/{username}")
async def update_user(
    username: str,
    body: dict,
    _=Depends(require_role(Role.ADMIN)),
):
    return AuthService.update_user(username, **body).dict_safe()


@router.delete("/users/{username}")
async def delete_user(
    username: str,
    _=Depends(require_role(Role.ADMIN)),
):
    AuthService.delete_user(username)
    return {"message": "User deleted"}
