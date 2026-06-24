from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.auth.models import Role, Token, TokenPayload, User
from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
USERS_FILE = Path(__file__).resolve().parent / "users.json"


def _load_users() -> dict[str, dict[str, Any]]:
    if not USERS_FILE.exists():
        return _create_default_users()
    try:
        raw = json.loads(USERS_FILE.read_text())
        # Pydantic auto-parses ISO datetime strings from JSON
        return {k: User(**v).model_dump() for k, v in raw.items()}
    except (json.JSONDecodeError, OSError, Exception):
        return _create_default_users()


def _save_users(users: dict[str, dict[str, Any]]) -> None:
    class _Encoder(json.JSONEncoder):
        def default(self, o: Any) -> str:
            if hasattr(o, "isoformat"):
                return o.isoformat()
            return str(o)
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2, cls=_Encoder))


def _create_default_users() -> dict[str, dict[str, Any]]:
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    users: dict[str, dict[str, Any]] = {
        admin_username: User(
            username=admin_username,
            password_hash=pwd_context.hash(admin_password),
            role=Role.ADMIN,
        ).model_dump(),
    }
    _save_users(users)
    return users


class AuthService:
    _users: dict[str, dict[str, Any]] = {}

    @classmethod
    def _get_users(cls) -> dict[str, dict[str, Any]]:
        if not cls._users:
            cls._users = _load_users()
        return cls._users

    @classmethod
    def _save(cls) -> None:
        _save_users(cls._users)

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def create_access_token(cls, username: str, role: Role) -> Token:
        expire = datetime.utcnow() + timedelta(minutes=480)
        payload = {
            "sub": username,
            "role": role.value,
            "exp": int(expire.timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
        return Token(access_token=token, expires_in=28800)

    @classmethod
    def decode_token(cls, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
            return TokenPayload(**payload)
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @classmethod
    def authenticate(cls, username: str, password: str) -> User | None:
        users = cls._get_users()
        data = users.get(username)
        if not data:
            return None
        user = User(**data)
        if not user.is_active:
            return None
        if not cls.verify_password(password, user.password_hash):
            return None
        user.last_login = datetime.utcnow()
        users[username] = user.model_dump()
        cls._save()
        return user

    @classmethod
    def get_user(cls, username: str) -> User | None:
        users = cls._get_users()
        data = users.get(username)
        if not data:
            return None
        return User(**data)

    @classmethod
    def list_users(cls) -> list[dict[str, Any]]:
        return [User(**u).dict_safe() for u in cls._get_users().values()]

    @classmethod
    def create_user(cls, username: str, password: str, role: Role) -> User:
        users = cls._get_users()
        if username in users:
            raise HTTPException(status_code=409, detail="User already exists")
        user = User(
            username=username,
            password_hash=cls.hash_password(password),
            role=role,
        )
        users[username] = user.model_dump()
        cls._save()
        return user

    @classmethod
    def update_user(cls, username: str, **kwargs: Any) -> User:
        users = cls._get_users()
        if username not in users:
            raise HTTPException(status_code=404, detail="User not found")
        user = User(**users[username])
        for k, v in kwargs.items():
            if k == "password":
                setattr(user, "password_hash", cls.hash_password(v))
            elif k == "role":
                setattr(user, "role", Role(v))
            elif hasattr(user, k):
                setattr(user, k, v)
        users[username] = user.model_dump()
        cls._save()
        return user

    @classmethod
    def delete_user(cls, username: str) -> None:
        users = cls._get_users()
        users.pop(username, None)
        cls._save()
