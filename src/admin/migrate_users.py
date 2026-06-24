"""Миграция пользователей из users.json в SQLite."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from src.admin.database import async_session, init_db
from src.admin.models import User
from src.auth.service import AuthService

USERS_JSON = Path(__file__).resolve().parent.parent / "auth" / "users.json"


async def migrate():
    if not USERS_JSON.exists():
        print("users.json не найден, создаю админа по умолчанию")
        async with async_session() as db:
            admin = User(
                username="admin",
                password_hash=AuthService.hash_password("admin123"),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            await db.commit()
        print("Создан admin / admin123")
        return

    with open(USERS_JSON) as f:
        data = json.load(f)

    async with async_session() as db:
        count = 0
        for username, user_data in data.items():
            existing = await db.get(User, username)
            if existing:
                continue
            user = User(
                username=username,
                password_hash=user_data.get("password_hash", AuthService.hash_password("password")),
                role=user_data.get("role", "viewer"),
                is_active=user_data.get("is_active", True),
                email=user_data.get("email"),
            )
            db.add(user)
            count += 1
        await db.commit()
        print(f"Мигрировано {count} пользователей")


if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(migrate())
