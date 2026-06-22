from __future__ import annotations

import pytest
import numpy as np
import pandas as pd

from src.whatif.scenarios.price_change import PriceChangeScenario, PriceChangeResult
from src.whatif.scenarios.promotion import PromotionScenario, PromotionParams
from src.whatif.scenarios.purchase_change import PurchaseChangeScenario, PurchaseChangeParams
from src.whatif.engine.financial_calculator import FinancialCalculator
from src.whatif.models.monte_carlo import MonteCarloSimulator


@pytest.fixture
def sales_df():
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=365, freq="D")
    prices = 100 + np.random.normal(0, 5, 365)
    qty = np.maximum(100 * (prices / 100) ** -0.7 * np.random.normal(1, 0.1, 365), 0)
    return pd.DataFrame({"date": dates, "price": prices, "quantity": qty})


@pytest.fixture
def qty_df():
    np.random.seed(42)
    return pd.DataFrame({"date": pd.date_range("2025-01-01", periods=180, freq="D"), "quantity": np.maximum(np.random.normal(100, 25, 180), 10)})


def test_price_change_simulate(sales_df):
    s = PriceChangeScenario()
    r = s.simulate(entity_name="Test", historical_data=sales_df, price_change_percent=10, cost_per_unit=60, period_days=30)
    assert isinstance(r, PriceChangeResult)
    assert r.baseline_price > 0
    assert len(r.recommendations) > 0


def test_price_change_increase(sales_df):
    s = PriceChangeScenario()
    r = s.simulate(entity_name="Test", historical_data=sales_df, price_change_percent=10, cost_per_unit=60)
    assert r.price_change_percent == 10
    assert r.volume_change_percent <= 0


def test_price_change_decrease(sales_df):
    s = PriceChangeScenario()
    r = s.simulate(entity_name="Test", historical_data=sales_df, price_change_percent=-10, cost_per_unit=60)
    assert r.volume_change_percent >= 0


def test_promotion_simulate(sales_df):
    s = PromotionScenario()
    params = PromotionParams(entity_name="Test", historical_data=sales_df, discount_percent=15, promotion_days=14, cost_per_unit=600)
    r = s.simulate(params)
    assert r.scenario_type == "promotion"
    assert len(r.recommendations) > 0


def test_promotion_large_discount(sales_df):
    s = PromotionScenario()
    params = PromotionParams(entity_name="Test", historical_data=sales_df, discount_percent=30, promotion_days=7, cost_per_unit=600, cannibalization_rate=0.3)
    r = s.simulate(params)
    assert r.projected_metrics.get("cannibalization", 0) > 0


def test_purchase_change(qty_df):
    s = PurchaseChangeScenario()
    params = PurchaseChangeParams(entity_name="Test", historical_data=qty_df, current_order_size=2000, current_order_frequency_days=20, purchase_price_per_unit=8, selling_price_per_unit=15, order_size_change_percent=50, avg_lost_sale_value=150000)
    r = s.simulate(params)
    assert r.scenario_type == "purchase_change"
    assert "frozen_money" in r.baseline_metrics


def test_purchase_reduces_stockout(qty_df):
    s = PurchaseChangeScenario()
    params = PurchaseChangeParams(entity_name="Test", historical_data=qty_df, current_order_size=500, current_order_frequency_days=30, purchase_price_per_unit=8, selling_price_per_unit=15, order_size_change_percent=100, avg_lost_sale_value=150000)
    r = s.simulate(params)
    assert r.projected_metrics["stockout_prob"] < r.baseline_metrics["stockout_prob"]


def test_financial_calculator_price():
    r = FinancialCalculator.calculate_price_change_impact(baseline_price=100, baseline_quantity=1000, baseline_cost_per_unit=60, price_change_percent=10, volume_change_percent=-5, period_days=30)
    assert r.revenue_delta > 0
    assert r.margin_delta > 0
    assert r.baseline_margin == 40000


def test_financial_calculator_investment():
    r = FinancialCalculator.calculate_investment_impact(baseline_revenue=100000, baseline_cost=80000, projected_revenue=120000, projected_cost=90000, investment_cost=300000, period_months=12)
    assert r.roi_percent is not None
    assert r.payback_months is not None


def test_monte_carlo():
    sim = MonteCarloSimulator(iterations=1000)
    r = sim.simulate(base_value=1_000_000, volatility=0.1)
    assert r.iterations == 1000
    assert r.median > 0
    assert r.confidence_interval[0] < r.confidence_interval[1]
