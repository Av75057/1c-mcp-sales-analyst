from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.arima.model import ARIMA

from src.forecasting.metrics import calc_metrics
from src.logger import logger


class ForecastModel(ABC):
    @abstractmethod
    def fit(self, df: pd.DataFrame) -> None:
        ...

    @abstractmethod
    def predict(self, days: int) -> pd.DataFrame:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


def _prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    df = df.copy().sort_values("date")
    if "ds" not in df.columns:
        df["ds"] = pd.to_datetime(df["date"])
    y = df["y"].values if "y" in df.columns else df["quantity"].values
    return df, y


class HoltWintersModel(ForecastModel):
    name = "Holt-Winters"

    def __init__(self) -> None:
        self.model: ETSModel | None = None
        self._fitted: Any = None
        self._history: pd.DataFrame = pd.DataFrame()

    def fit(self, df: pd.DataFrame) -> None:
        df, y = _prepare(df)
        self._history = df
        self.model = ETSModel(y, seasonal_periods=7, error="add", trend="add", seasonal="add")
        self._fitted = self.model.fit(disp=False)
        logger.info("Holt-Winters обучена на {} точках", len(df))

    def predict(self, days: int) -> pd.DataFrame:
        if self._fitted is None:
            return pd.DataFrame()
        fc = self._fitted.forecast(days)
        last_date = self._history["ds"].max()
        dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=days)
        return pd.DataFrame({"ds": dates, "yhat": fc.values, "yhat_lower": fc.values * 0.9, "yhat_upper": fc.values * 1.1})


class LinearModel(ForecastModel):
    name = "Linear Regression"

    def __init__(self) -> None:
        self.model = LinearRegression()
        self._history: pd.DataFrame = pd.DataFrame()

    def fit(self, df: pd.DataFrame) -> None:
        df, y = _prepare(df)
        self._history = df
        X = np.arange(len(y)).reshape(-1, 1)
        self.model.fit(X, y)
        logger.info("Linear обучена на {} точках", len(df))

    def predict(self, days: int) -> pd.DataFrame:
        if len(self._history) == 0:
            return pd.DataFrame()
        last_date = self._history["ds"].max()
        dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=days)
        X_new = np.arange(len(self._history), len(self._history) + days).reshape(-1, 1)
        yhat = self.model.predict(X_new)
        resid = np.std(self._history["y"].values - self.model.predict(np.arange(len(self._history)).reshape(-1, 1)))
        return pd.DataFrame({"ds": dates, "yhat": yhat, "yhat_lower": yhat - 1.96 * resid, "yhat_upper": yhat + 1.96 * resid})


class ARIMAModel(ForecastModel):
    name = "ARIMA"

    def __init__(self) -> None:
        self.model: ARIMA | None = None
        self._fitted: Any = None
        self._history: pd.DataFrame = pd.DataFrame()

    def fit(self, df: pd.DataFrame) -> None:
        df, y = _prepare(df)
        self._history = df
        try:
            self.model = ARIMA(y, order=(7, 1, 2))
            self._fitted = self.model.fit()
            logger.info("ARIMA обучена на {} точках", len(df))
        except Exception as e:
            logger.warning("ARIMA fallback: {}", e)

    def predict(self, days: int) -> pd.DataFrame:
        if self._fitted is None:
            return pd.DataFrame()
        fc = self._fitted.forecast(days)
        last_date = self._history["ds"].max()
        dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=days)
        return pd.DataFrame({"ds": dates, "yhat": fc.values, "yhat_lower": fc.values * 0.85, "yhat_upper": fc.values * 1.15})


class ProphetModel(ForecastModel):
    name = "Prophet"

    def __init__(self) -> None:
        self.model: Any = None
        self._history: pd.DataFrame = pd.DataFrame()

    def fit(self, df: pd.DataFrame) -> None:
        from prophet import Prophet
        df_p = df.copy()
        if "ds" not in df_p.columns:
            df_p["ds"] = pd.to_datetime(df_p["date"])
        if "y" not in df_p.columns:
            df_p["y"] = df_p["quantity"]
        self._history = df_p
        self.model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        self.model.fit(df_p[["ds", "y"]])
        logger.info("Prophet обучена на {} точках", len(df_p))

    def predict(self, days: int) -> pd.DataFrame:
        if self.model is None:
            return pd.DataFrame()
        future = self.model.make_future_dataframe(periods=days)
        fc = self.model.predict(future)
        last_idx = len(self._history)
        return fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].iloc[last_idx:].reset_index(drop=True)


def auto_select(df: pd.DataFrame) -> ForecastModel:
    n = len(df)
    if n < 14:
        return LinearModel()
    if n < 60:
        return HoltWintersModel()
    try:
        m = ProphetModel()
        m.fit(df)
        return m
    except Exception:
        return HoltWintersModel()
