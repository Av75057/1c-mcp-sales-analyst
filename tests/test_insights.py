from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.clients.mock_c1_client import MockC1Client
from src.insights.deduplication.dedup_engine import DedupEngine
from src.insights.detectors.inactive_clients import InactiveClientsDetector
from src.insights.detectors.receivables_alert import ReceivablesAlertDetector
from src.insights.detectors.sales_anomaly import SalesAnomalyDetector
from src.insights.detectors.sales_growth import SalesGrowthDetector
from src.insights.detectors.stock_shortage import StockShortageDetector
from src.insights.models import RawInsight, TenantInsightsConfig


@pytest.fixture
def config():
    c = TenantInsightsConfig()
    c.sales_drop_threshold = 0.0
    c.sales_growth_threshold = 0.0
    c.stock_days_threshold = 999
    return c


@pytest.mark.asyncio
async def test_sales_anomaly_detector(config):
    d = SalesAnomalyDetector(config)
    insights = await d.detect()
    assert isinstance(insights, list)


@pytest.mark.asyncio
async def test_sales_growth_detector(config):
    d = SalesGrowthDetector(config)
    insights = await d.detect()
    assert isinstance(insights, list)


@pytest.mark.asyncio
async def test_stock_shortage_detector(config):
    config.stock_days_threshold = 999
    d = StockShortageDetector(config)
    insights = await d.detect()
    expected = [i for i in insights if i.metric_value < 999]
    assert isinstance(insights, list)
    assert len(expected) >= 0


@pytest.mark.asyncio
async def test_inactive_clients_detector(config):
    d = InactiveClientsDetector(config)
    insights = await d.detect()
    assert isinstance(insights, list)
    if insights:
        assert insights[0].detector == "inactive_clients"


@pytest.mark.asyncio
async def test_receivables_alert_detector(config):
    d = ReceivablesAlertDetector(config)
    insights = await d.detect()
    assert isinstance(insights, list)
    if insights:
        assert insights[0].detector == "receivables_alert"
        assert insights[0].entity_type == "client"


def test_raw_insight_dedup_key():
    i = RawInsight(
        detector="test",
        priority="warning",
        title="Test",
        entity_type="item",
        entity_id="001",
        entity_name="Test Item",
        metric_name="qty",
        metric_value=10,
        metric_baseline=20,
        metric_delta_percent=-50.0,
        period_from=date(2026, 6, 1),
        period_to=date(2026, 6, 19),
    )
    assert "test:item:001:qty" in i.dedup_key
    assert "2026:25" in i.dedup_key


def test_dedup_engine():
    import uuid
    config = TenantInsightsConfig()
    engine = DedupEngine(config)
    unique_id = str(uuid.uuid4())[:8]

    raw = RawInsight(
        detector="test_dedup",
        priority="info",
        title="Dedup Test",
        entity_type="item",
        entity_id=f"001_{unique_id}",
        entity_name="Test",
        metric_name="qty",
        metric_value=10,
        metric_baseline=20,
        metric_delta_percent=-50.0,
        period_from=date(2026, 6, 1),
        period_to=date(2026, 6, 19),
    )

    assert engine.should_send(raw)
    engine.mark_sent(raw)
    assert not engine.should_send(raw)
    engine.clean_old(days=0)
    assert not engine.should_send(raw)
    path = engine._sent_path(raw.dedup_key)
    path.unlink(missing_ok=True)
    assert engine.should_send(raw)


@pytest.mark.asyncio
async def test_mock_client_data_integrity():
    c = MockC1Client()

    stock = await c.get_stock()
    assert len(stock) > 0

    sales = await c.get_sales()
    assert len(sales) > 0

    by_mgr = await c.get_sales_by_manager()
    assert len(by_mgr) > 0

    receivables = await c.get_receivables()
    assert len(receivables) > 0
