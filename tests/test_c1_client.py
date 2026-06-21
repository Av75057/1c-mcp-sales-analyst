from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.clients.c1_client import C1Client, C1ClientError


@pytest.fixture
def mock_httpx_client():
    with patch("src.clients.c1_client.C1Client._get_client", new_callable=AsyncMock) as mock:
        yield mock


@pytest.mark.asyncio
async def test_get_stock_success(mock_httpx_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"item": "Гвоздь 100мм", "quantity": 150}]
    mock_httpx_client.return_value.get = AsyncMock(return_value=mock_resp)

    c = C1Client()
    result = await c.get_stock()
    assert len(result) == 1
    assert result[0]["nomenclature"] == "Гвоздь 100мм"


@pytest.mark.asyncio
async def test_get_sales_success(mock_httpx_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"date": "2026-06-18", "item": "Гвоздь", "quantity": 10, "sum": 1250, "manager": "Иванов"}]
    mock_httpx_client.return_value.get = AsyncMock(return_value=mock_resp)

    c = C1Client()
    result = await c.get_sales()
    assert len(result) == 1
    assert result[0]["nomenclature"] == "Гвоздь"


@pytest.mark.asyncio
async def test_get_stock_with_filters(mock_httpx_client):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = []
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_httpx_client.return_value = mock_client

    c = C1Client()
    await c.get_stock(warehouse="Москва", nomenclature="Гвоздь", min_quantity=100)

    params = mock_client.get.call_args[1].get("params", {})
    assert params.get("organization") or params.get("item")


@pytest.mark.asyncio
async def test_empty_response(mock_httpx_client):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = []
    mock_httpx_client.return_value.get = AsyncMock(return_value=mock_resp)

    c = C1Client()
    result = await c.get_stock()
    assert result == []


@pytest.mark.asyncio
async def test_get_receivables(mock_httpx_client):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = [{"client": "ООО Ромашка", "amount": 125000, "overdue_days": 45}]
    mock_httpx_client.return_value.get = AsyncMock(return_value=mock_resp)

    c = C1Client()
    result = await c.get_receivables()
    assert result[0]["client"] == "ООО Ромашка"


@pytest.mark.asyncio
async def test_list_nomenclature(mock_httpx_client):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = [{"ref": "NG-001", "name": "Гвоздь 100мм", "unit": "шт"}]
    mock_httpx_client.return_value.get = AsyncMock(return_value=mock_resp)

    c = C1Client()
    result = await c.list_nomenclature("Гвоздь")
    assert result[0]["name"] == "Гвоздь 100мм"


@pytest.mark.asyncio
async def test_ping_success(mock_httpx_client):
    mock_resp = MagicMock(status_code=200)
    mock_httpx_client.return_value.get = AsyncMock(return_value=mock_resp)

    c = C1Client()
    assert await c.ping() is True


@pytest.mark.asyncio
async def test_ping_failure(mock_httpx_client):
    mock_httpx_client.return_value.get = AsyncMock(side_effect=Exception("Connection failed"))

    c = C1Client()
    assert await c.ping() is False


@pytest.mark.asyncio
async def test_close(mock_httpx_client):
    c = C1Client()
    await c._get_client()
    await c.close()
    assert c._client is None
