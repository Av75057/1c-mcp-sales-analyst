from __future__ import annotations

import os

os.environ["AUTH_ENABLED"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-key-phase4-integration"

from src.config import settings

settings.reload()

from fastapi.testclient import TestClient

from web.app import app

client = TestClient(app)


def _login() -> str:
    r = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def _headers():
    return {"Authorization": f"Bearer {_login()}"}


class TestAnonymizationAPI:
    def test_stats(self):
        r = client.get("/api/anonymization/stats", headers=_headers())
        assert r.status_code == 200
        data = r.json()
        assert "total_tokens" in data

    def test_stats_requires_auth(self):
        r = client.get("/api/anonymization/stats")
        assert r.status_code in (302, 401)


class TestMetadataAPI:
    def test_config(self):
        r = client.get("/api/metadata/config", headers=_headers())
        assert r.status_code == 200
        assert "name" in r.json()

    def test_describe(self):
        r = client.get("/api/metadata/describe", headers=_headers())
        assert r.status_code == 200
        assert "objects" in r.json()

    def test_describe_by_type(self):
        r = client.get("/api/metadata/describe?type=Catalog", headers=_headers())
        assert r.status_code == 200

    def test_structure(self):
        r = client.get("/api/metadata/structure/Номенклатура", headers=_headers())
        assert r.status_code == 200
        assert r.json()["name"] == "Номенклатура"

    def test_cache_invalidate(self):
        r = client.post("/api/metadata/cache/invalidate", headers=_headers())
        assert r.status_code == 200
