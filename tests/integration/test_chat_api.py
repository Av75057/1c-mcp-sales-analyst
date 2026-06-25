from __future__ import annotations

import json
import os

os.environ["AUTH_ENABLED"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-chat-api-tests-12345"

from fastapi.testclient import TestClient

from src.config import settings

settings.reload()

from web.app import app

client = TestClient(app)


def _login() -> str:
    r = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


class TestChatAPI:
    def _headers(self):
        return {"Authorization": f"Bearer {_login()}"}

    def test_list_sessions_returns_list(self):
        r = client.get("/api/chat/sessions", headers=self._headers())
        assert r.status_code == 200
        assert isinstance(r.json()["sessions"], list)

    def test_create_session(self):
        r = client.post("/api/chat/sessions", headers=self._headers(), json={})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["title"] == "Новый чат"

    def test_create_session_with_title(self):
        r = client.post("/api/chat/sessions", headers=self._headers(), json={"title": "My Chat"})
        assert r.status_code == 200
        assert r.json()["title"] == "My Chat"

    def test_get_session(self):
        sid = client.post("/api/chat/sessions", headers=self._headers(), json={}).json()["id"]
        r = client.get(f"/api/chat/sessions/{sid}", headers=self._headers())
        assert r.status_code == 200
        assert r.json()["id"] == sid

    def test_get_session_not_found(self):
        r = client.get("/api/chat/sessions/nonexistent", headers=self._headers())
        assert r.status_code == 404

    def test_update_session_title(self):
        sid = client.post("/api/chat/sessions", headers=self._headers(), json={}).json()["id"]
        r = client.put(f"/api/chat/sessions/{sid}", headers=self._headers(), json={"title": "Updated"})
        assert r.status_code == 200
        get = client.get(f"/api/chat/sessions/{sid}", headers=self._headers())
        assert get.json()["title"] == "Updated"

    def test_delete_session(self):
        sid = client.post("/api/chat/sessions", headers=self._headers(), json={}).json()["id"]
        r = client.delete(f"/api/chat/sessions/{sid}", headers=self._headers())
        assert r.status_code == 200
        get = client.get(f"/api/chat/sessions/{sid}", headers=self._headers())
        assert get.status_code == 404

    def test_get_messages_empty(self):
        sid = client.post("/api/chat/sessions", headers=self._headers(), json={}).json()["id"]
        r = client.get(f"/api/chat/sessions/{sid}/messages", headers=self._headers())
        assert r.status_code == 200
        assert r.json()["messages"] == []

    def test_send_message(self):
        sid = client.post("/api/chat/sessions", headers=self._headers(), json={}).json()["id"]
        r = client.post(f"/api/chat/sessions/{sid}/messages", headers=self._headers(), json={"content": "привет"})
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert len(data["answer"]) > 0

    def test_send_message_saves_history(self):
        sid = client.post("/api/chat/sessions", headers=self._headers(), json={}).json()["id"]
        client.post(f"/api/chat/sessions/{sid}/messages", headers=self._headers(), json={"content": "тест"})
        hist = client.get(f"/api/chat/sessions/{sid}/messages", headers=self._headers()).json()
        assert len(hist["messages"]) >= 2

    def test_send_empty_message_returns_400(self):
        sid = client.post("/api/chat/sessions", headers=self._headers(), json={}).json()["id"]
        r = client.post(f"/api/chat/sessions/{sid}/messages", headers=self._headers(), json={"content": ""})
        assert r.status_code == 400

    def test_search_messages(self):
        sid = client.post("/api/chat/sessions", headers=self._headers(), json={}).json()["id"]
        client.post(f"/api/chat/sessions/{sid}/messages", headers=self._headers(), json={"content": "продажи за январь"})
        r = client.get("/api/chat/search?q=январь", headers=self._headers())
        assert r.status_code == 200
        assert len(r.json()["results"]) >= 1

    def test_export_session(self):
        sid = client.post("/api/chat/sessions", headers=self._headers(), json={}).json()["id"]
        client.post(f"/api/chat/sessions/{sid}/messages", headers=self._headers(), json={"content": "экспорт"})
        r = client.get(f"/api/chat/sessions/{sid}/export", headers=self._headers())
        assert r.status_code == 200
        assert "messages" in r.json()

    def test_sessions_returns_all(self):
        client.post("/api/chat/sessions", headers=self._headers(), json={"title": "A"}).json()
        client.post("/api/chat/sessions", headers=self._headers(), json={"title": "B"}).json()
        r = client.get("/api/chat/sessions", headers=self._headers())
        assert len(r.json()["sessions"]) >= 2

    def test_requires_auth(self):
        r = client.get("/api/chat/sessions", follow_redirects=False)
        assert r.status_code in (302, 401)
