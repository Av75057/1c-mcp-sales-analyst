from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import Role, Token, TokenPayload, User
from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
USERS_FILE = Path(__file__).resolve().parent / "users.json"


class AuthService:

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(username: str, role: str, extra: dict | None = None) -> Token:
        expire = datetime.utcnow() + timedelta(minutes=480)
        payload = {
            "sub": username,
            "role": role,
            "exp": int(expire.timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
        }
        if extra:
            payload.update(extra)
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
        return Token(access_token=token, expires_in=28800)

    @staticmethod
    def decode_token(token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
            return TokenPayload(**payload)
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> User | None:
        from src.admin.models import User as DBUser

        result = await db.execute(select(DBUser).where(DBUser.username == username))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        if not db_user.is_active:
            return None
        if db_user.locked_until and db_user.locked_until > datetime.utcnow():
            return None
        if not AuthService.verify_password(password, db_user.password_hash):
            db_user.failed_login_attempts = (db_user.failed_login_attempts or 0) + 1
            await db.commit()
            return None
        db_user.failed_login_attempts = 0
        db_user.last_login = datetime.utcnow()
        db_user.locked_until = None
        await db.commit()
        return User(username=db_user.username, role=Role(db_user.role), is_active=db_user.is_active)

    @staticmethod
    async def get_user(db: AsyncSession, username: str) -> User | None:
        from src.admin.models import User as DBUser

        result = await db.execute(select(DBUser).where(DBUser.username == username))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return User(username=db_user.username, role=Role(db_user.role), is_active=db_user.is_active)

    @staticmethod
    async def create_user(db: AsyncSession, username: str, password: str, role: str, email: str | None = None) -> User:
        from src.admin.models import User as DBUser

        user = DBUser(username=username, password_hash=AuthService.hash_password(password), role=role, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return User(username=user.username, role=Role(user.role), is_active=user.is_active)

    @staticmethod
    async def list_users(db: AsyncSession) -> list[dict[str, Any]]:
        from src.admin.models import User as DBUser

        result = await db.execute(select(DBUser).order_by(DBUser.created_at.desc()))
        return [
            {
                "username": u.username,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in result.scalars().all()
        ]
