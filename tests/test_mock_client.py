from __future__ import annotations

import pytest

from src.clients.mock_c1_client import MockC1Client


@pytest.fixture
async def client():
    c = MockC1Client()
    yield c
    await c.close()


@pytest.mark.asyncio
async def test_get_stock(client):
    data = await client.get_stock()
    assert len(data) > 0
    assert "nomenclature" in data[0]
    assert "warehouse" in data[0]
    assert "quantity" in data[0]
    assert "unit" in data[0]
    assert data[0]["quantity"] >= 0


@pytest.mark.asyncio
async def test_get_stock_filter_warehouse(client):
    data = await client.get_stock(warehouse="Москва")
    assert all(d["warehouse"] == "Москва" for d in data)


@pytest.mark.asyncio
async def test_get_stock_filter_nomenclature(client):
    data = await client.get_stock(nomenclature="гвоздь")
    assert all("гвоздь" in d["nomenclature"].lower() for d in data)


@pytest.mark.asyncio
async def test_get_stock_filter_min_quantity(client):
    data = await client.get_stock(min_quantity=1000)
    assert all(d["quantity"] >= 1000 for d in data)


@pytest.mark.asyncio
async def test_get_stock_no_results(client):
    data = await client.get_stock(nomenclature="nonexistent_xyz_123")
    assert data == []


@pytest.mark.asyncio
async def test_get_sales(client):
    data = await client.get_sales()
    assert len(data) > 0
    assert "date" in data[0]
    assert "nomenclature" in data[0]
    assert "quantity" in data[0]
    assert "sum" in data[0]
    assert "manager" in data[0]


@pytest.mark.asyncio
async def test_get_sales_date_filter(client):
    data = await client.get_sales(date_from="2099-01-01", date_to="2099-12-31")
    assert data == []


@pytest.mark.asyncio
async def test_get_sales_manager_filter(client):
    data = await client.get_sales(manager="Иванов")
    assert all("Иванов" in d["manager"] for d in data)


@pytest.mark.asyncio
async def test_get_sales_by_manager(client):
    data = await client.get_sales_by_manager()
    assert len(data) > 0
    assert "manager" in data[0]
    assert "total_sum" in data[0]
    assert "total_quantity" in data[0]


@pytest.mark.asyncio
async def test_get_receivables(client):
    data = await client.get_receivables()
    assert len(data) > 0
    assert "client" in data[0]
    assert "amount" in data[0]
    assert "overdue_days" in data[0]


@pytest.mark.asyncio
async def test_get_receivables_min_amount(client):
    data = await client.get_receivables(min_amount=1_000_000)
    assert data == []


@pytest.mark.asyncio
async def test_list_nomenclature(client):
    data = await client.list_nomenclature(query="гвоздь")
    assert len(data) > 0
    assert "ref" in data[0]
    assert "name" in data[0]


@pytest.mark.asyncio
async def test_list_nomenclature_no_results(client):
    data = await client.list_nomenclature(query="xyz_nonexistent")
    assert data == []
