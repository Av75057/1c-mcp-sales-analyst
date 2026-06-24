from __future__ import annotations

import os
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Создаём отдельное приложение для тестов админки (с AUTH_ENABLED=true)
os.environ["AUTH_ENABLED"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-admin-tests-1234567890"

from src.config import settings

settings.reload()

from web.app import app as _original_app

# Создаём новый app для тестов, чтобы не менять глобальное состояние
app = FastAPI(title="Admin Test", version="1.0.0")

from src.auth.middleware import AuthMiddleware
from src.auth.routes import router as auth_router
from src.security.headers import SecurityHeadersMiddleware
from src.security.rate_limit import init_rate_limiter

from src.admin.routes.dashboard import router as admin_dashboard_router
from src.admin.routes.users import router as admin_users_router
from src.admin.routes.audit import router as admin_audit_router
from src.admin.routes.monitoring import router as admin_monitoring_router
from src.admin.routes.settings import router as admin_settings_router
from src.admin.routes.integrations import router as admin_integrations_router
from src.admin.routes.tools_route import router as admin_tools_router
from src.admin.routes.system import router as admin_system_router
from src.admin.routes.api_keys import router as admin_api_keys_router
from src.admin.routes.ip_block import router as admin_ip_blocks_router

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuthMiddleware)
init_rate_limiter(app)
app.include_router(auth_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_users_router)
app.include_router(admin_audit_router)
app.include_router(admin_monitoring_router)
app.include_router(admin_settings_router)
app.include_router(admin_integrations_router)
app.include_router(admin_tools_router)
app.include_router(admin_system_router)
app.include_router(admin_api_keys_router)
app.include_router(admin_ip_blocks_router)

client = TestClient(app)

AUTH_DATA = {"username": "admin", "password": "admin123"}


def _login() -> str:
    r = client.post("/api/auth/login", data=AUTH_DATA)
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(autouse=True)
def _ensure_admin():
    """Создаём admin если его нет в БД для этого тестового запуска"""
    from src.admin.database import async_session, init_db
    from src.admin.models import User
    from src.auth.service import AuthService
    from sqlalchemy import select
    import asyncio

    async def _init():
        await init_db()
        async with async_session() as db:
            r = await db.execute(select(User).where(User.username == "admin"))
            if not r.scalar_one_or_none():
                db.add(User(username="admin", password_hash=AuthService.hash_password("admin123"), role="admin", is_active=True))
                await db.commit()

    asyncio.run(_init())
    yield


class TestAdminDashboard:
    def test_dashboard_json(self):
        token = _login()
        r = client.get("/admin/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data
        assert "alerts" in data

    def test_dashboard_requires_admin(self):
        uname = f"no_admin_{int(time.time())}"
        token = _login()
        r = client.post("/admin/users/", headers={"Authorization": f"Bearer {token}"}, json={"username": uname, "password": "test123", "role": "analyst"})
        assert r.status_code == 200
        r2 = client.post("/api/auth/login", data={"username": uname, "password": "test123"})
        assert r2.status_code == 200
        token2 = r2.json()["access_token"]
        r3 = client.get("/admin/", headers={"Authorization": f"Bearer {token2}"})
        assert r3.status_code == 403


class TestAdminUsers:
    def test_list_users(self):
        token = _login()
        r = client.get("/admin/users/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        users = r.json()
        assert isinstance(users, list)
        assert any(u["username"] == "admin" for u in users)

    def test_create_user(self):
        token = _login()
        uname = f"create_{int(time.time())}"
        r = client.post("/admin/users/", headers={"Authorization": f"Bearer {token}"}, json={"username": uname, "password": "pass123", "role": "analyst"})
        assert r.status_code == 200
        assert r.json()["username"] == uname
        assert r.json()["role"] == "analyst"

    def test_create_duplicate(self):
        token = _login()
        uname = f"dup_{int(time.time())}"
        client.post("/admin/users/", headers={"Authorization": f"Bearer {token}"}, json={"username": uname, "password": "p", "role": "viewer"})
        r2 = client.post("/admin/users/", headers={"Authorization": f"Bearer {token}"}, json={"username": uname, "password": "p", "role": "viewer"})
        assert r2.status_code == 409

    def test_get_user(self):
        token = _login()
        r = client.get("/admin/users/1", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "admin"

    def test_update_user(self):
        token = _login()
        uname = f"upd_{int(time.time())}"
        r = client.post("/admin/users/", headers={"Authorization": f"Bearer {token}"}, json={"username": uname, "password": "p", "role": "viewer"})
        uid = r.json()["id"]
        r2 = client.patch(f"/admin/users/{uid}", headers={"Authorization": f"Bearer {token}"}, json={"role": "analyst"})
        assert r2.status_code == 200
        assert r2.json()["role"] == "analyst"

    def test_delete_user(self):
        token = _login()
        uname = f"del_{int(time.time())}"
        r = client.post("/admin/users/", headers={"Authorization": f"Bearer {token}"}, json={"username": uname, "password": "p", "role": "viewer"})
        uid = r.json()["id"]
        r2 = client.delete(f"/admin/users/{uid}", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200

    def test_cannot_delete_self(self):
        token = _login()
        r = client.delete("/admin/users/1", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 400

    def test_block_unblock(self):
        token = _login()
        r = client.post("/admin/users/1/block", headers={"Authorization": f"Bearer {token}"}, json={"minutes": 1})
        assert r.status_code == 200
        r2 = client.post("/admin/users/1/unblock", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200

    def test_reset_sessions(self):
        token = _login()
        r = client.post("/admin/users/1/reset-sessions", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200


class TestAdminAudit:
    def test_logs(self):
        token = _login()
        r = client.get("/admin/audit/?limit=10", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200 and "logs" in r.json()

    def test_stats(self):
        token = _login()
        r = client.get("/admin/audit/stats", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_export(self):
        token = _login()
        r = client.get("/admin/audit/export", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200 and "csv" in r.headers.get("content-type", "")


class TestAdminSettings:
    def test_list(self):
        token = _login()
        r = client.get("/admin/settings/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200 and "settings" in r.json()

    def test_get(self):
        token = _login()
        r = client.get("/admin/settings/CACHE_TTL_SECONDS", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_update(self):
        token = _login()
        r = client.put("/admin/settings/CACHE_TTL_SECONDS", headers={"Authorization": f"Bearer {token}"}, json={"value": "600", "category": "cache"})
        assert r.status_code == 200

    def test_history(self):
        token = _login()
        r = client.get("/admin/settings/CACHE_TTL_SECONDS/history", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_seed(self):
        token = _login()
        r = client.post("/admin/settings/seed", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200


class TestAdminMonitoring:
    def test_monitoring(self):
        token = _login()
        r = client.get("/admin/monitoring/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200 and "dashboard" in r.json()


class TestAdminIntegrations:
    def test_list(self):
        token = _login()
        r = client.get("/admin/integrations/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200 and "services" in r.json()

    def test_check(self):
        token = _login()
        r = client.get("/admin/integrations/check/1c", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200


class TestAdminTools:
    def test_list(self):
        token = _login()
        r = client.get("/admin/tools/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200 and len(r.json()["tools"]) > 0

    def test_stats(self):
        token = _login()
        r = client.get("/admin/tools/stats", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_calls(self):
        token = _login()
        r = client.get("/admin/tools/calls?limit=5", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200


class TestAdminApiKeys:
    def test_list(self):
        token = _login()
        r = client.get("/admin/api-keys/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200 and "keys" in r.json()

    def test_create_revoke(self):
        token = _login()
        r = client.post("/admin/api-keys/", headers={"Authorization": f"Bearer {token}"}, json={"name": "Test", "user_id": 1})
        assert r.status_code == 200 and "plain_key" in r.json()
        key_id = r.json()["info"]["id"]
        r2 = client.post(f"/admin/api-keys/{key_id}/revoke", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200


class TestAdminIpBlocks:
    def test_list(self):
        token = _login()
        r = client.get("/admin/ip-blocks/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200 and "blocks" in r.json()

    def test_block_unblock(self):
        token = _login()
        ts = int(time.time())
        r = client.post("/admin/ip-blocks/", headers={"Authorization": f"Bearer {token}"}, json={"ip_address": f"10.0.0.{ts % 255}", "reason": "test", "hours": 1})
        assert r.status_code == 200
        r2 = client.post("/admin/ip-blocks/1/unblock", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200

    def test_block_permanent(self):
        token = _login()
        ts = int(time.time())
        r = client.post("/admin/ip-blocks/", headers={"Authorization": f"Bearer {token}"}, json={"ip_address": f"10.0.0.{(ts+1) % 255}", "reason": "perm", "permanent": True})
        assert r.status_code == 200


class TestAdminSystem:
    def test_system(self):
        token = _login()
        r = client.get("/admin/system/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert "python_version" in r.json()
