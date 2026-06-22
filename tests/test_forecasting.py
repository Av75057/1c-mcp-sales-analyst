from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.forecasting.metrics import calc_metrics
from src.forecasting.models import LinearModel, HoltWintersModel, auto_select
from src.forecasting.stockout import predict_stockout


@pytest.fixture
def daily_df():
    np.random.seed(42)
    dates = pd.date_range("2026-01-01", periods=60, freq="D")
    trend = np.linspace(0, 30, 60)
    seasonal = 10 * np.sin(2 * np.pi * np.arange(60) / 7)
    noise = np.random.normal(0, 5, 60)
    values = np.maximum(100 + trend + seasonal + noise, 0)
    return pd.DataFrame({"date": dates, "quantity": values})


def test_linear_model_fit_predict(daily_df):
    m = LinearModel()
    m.fit(daily_df)
    pred = m.predict(7)
    assert len(pred) == 7
    assert "yhat" in pred.columns
    assert "yhat_lower" in pred.columns
    assert "yhat_upper" in pred.columns
    assert pred["yhat"].iloc[0] > 0


def test_holt_winters_fit_predict(daily_df):
    m = HoltWintersModel()
    m.fit(daily_df)
    pred = m.predict(7)
    assert len(pred) == 7
    assert pred["yhat"].iloc[0] > 0


def test_auto_select_returns_model(daily_df):
    m = auto_select(daily_df)
    assert m is not None
    m.fit(daily_df)
    pred = m.predict(7)
    assert len(pred) == 7


def test_auto_select_small_data():
    df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=10, freq="D"), "quantity": [100] * 10})
    m = auto_select(df)
    assert isinstance(m, LinearModel)


def test_calc_metrics():
    y_true = [100, 110, 120, 130]
    y_pred = [105, 108, 125, 128]
    m = calc_metrics(y_true, y_pred)
    assert "mape" in m
    assert "rmse" in m
    assert "mae" in m
    assert "r2" in m
    assert m["mape"] > 0
    assert m["r2"] < 1


def test_calc_metrics_perfect():
    y = [100, 200, 300]
    m = calc_metrics(y, y)
    assert m["mape"] == 0
    assert m["r2"] == 1.0


def test_stockout_empty_data():
    r = asyncio_run(predict_stockout([], []))
    assert "error" in r


def test_stockout_normal():
    stock = [{"nomenclature": "Тест", "quantity": 100}]
    sales = [{"nomenclature": "Тест", "quantity": 10, "date": "2026-01-01"} for _ in range(10)]
    r = asyncio_run(predict_stockout(stock, sales, lead_time_days=3, safety_stock_days=2))
    assert r["summary"]["total_items_analyzed"] == 1
    assert "critical" in r


def test_stockout_critical():
    stock = [{"nomenclature": "Хитрый", "quantity": 5}]
    sales = [{"nomenclature": "Хитрый", "quantity": 10, "date": "2026-01-01"} for _ in range(5)]
    r = asyncio_run(predict_stockout(stock, sales, lead_time_days=7, safety_stock_days=3))
    assert len(r["critical"]) == 1
    assert r["critical"][0]["status"] == "CRITICAL"


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)
