from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


class User(BaseModel):
    username: str
    password_hash: str = ""
    role: Role = Role.VIEWER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime | None = None

    def dict_safe(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 28800


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int
    iat: int
