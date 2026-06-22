from __future__ import annotations

import os

os.environ["USE_MOCK_DATA"] = "true"

import pytest
from fastapi.testclient import TestClient
from web.app import app

client = TestClient(app)


@pytest.mark.skip(reason="requires 1C connection")
def test_dashboard():
    r = client.get("/api/dashboard")
    assert r.status_code == 200


def test_status():
    r = client.get("/api/status")
    assert r.status_code == 200


def test_abc_xyz():
    r = client.get("/api/analysis/abc-xyz?date_from=2020-01-01&date_to=2020-12-31")
    assert r.status_code == 200


def test_simulate():
    r = client.post("/api/simulate", data={"scenario_type": "price_change", "entity_name": "Тест", "change_percent": "10"})
    assert r.status_code == 200


def test_html_pages():
    for path in ["/", "/chat", "/whatif", "/forecast"]:
        r = client.get(path)
        assert r.status_code == 200, f"{path} {r.status_code}"
