from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib

from src.logger import logger

MODEL_CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "models_cache"


@dataclass
class ElasticityResult:
    elasticity: float
    confidence: float
    r2_score: float
    mape: float
    is_elastic: bool
    price_change_percent: float
    volume_change_percent: float
    model_trained: bool


class ElasticityModel:
    def __init__(self) -> None:
        self.model = Ridge(alpha=1.0)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.elasticity_coefficient: float | None = None
        self.r2: float | None = None
        self.mape: float | None = None
        MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, entity_id: str) -> Path:
        safe = entity_id.replace("/", "_").replace(" ", "_")
        return MODEL_CACHE_DIR / f"elasticity_{safe}.pkl"

    def fit(self, df: pd.DataFrame) -> ElasticityResult:
        logger.info("ElasticityModel: обучение на {} записях", len(df))
        df = df[(df["price"] > 0) & (df["quantity"] > 0)].copy()
        if len(df) < 10:
            logger.warning("Недостаточно данных: {} < 10", len(df))
            return ElasticityResult(elasticity=-0.5, confidence=0.0, r2_score=0.0, mape=1.0, is_elastic=False, price_change_percent=0.0, volume_change_percent=0.0, model_trained=False)

        df["log_price"] = np.log(df["price"])
        df["log_quantity"] = np.log(df["quantity"])
        features = ["log_price"]

        if "weekday" in df.columns:
            df["weekday_sin"] = np.sin(2 * np.pi * df["weekday"] / 7)
            df["weekday_cos"] = np.cos(2 * np.pi * df["weekday"] / 7)
            features += ["weekday_sin", "weekday_cos"]
        if "is_promo" in df.columns:
            features.append("is_promo")
        df["time_index"] = np.arange(len(df))
        features.append("time_index")

        X = self.scaler.fit_transform(df[features].values)
        y = df["log_quantity"].values
        self.model.fit(X, y)
        y_pred = self.model.predict(X)
        self.r2 = r2_score(y, y_pred)
        self.mape = mean_absolute_percentage_error(np.exp(y), np.exp(y_pred))
        price_idx = features.index("log_price")
        self.elasticity_coefficient = float(self.model.coef_[price_idx])
        self.is_trained = True

        logger.info("Обучена: E={:.3f}, R²={:.3f}, MAPE={:.3f}", self.elasticity_coefficient, self.r2, self.mape)
        return ElasticityResult(elasticity=self.elasticity_coefficient, confidence=max(0.0, self.r2), r2_score=self.r2, mape=self.mape, is_elastic=abs(self.elasticity_coefficient) > 1, price_change_percent=0.0, volume_change_percent=0.0, model_trained=True)

    def predict(self, price_change_percent: float) -> ElasticityResult:
        if not self.is_trained:
            return ElasticityResult(elasticity=-0.5, confidence=0.0, r2_score=0.0, mape=1.0, is_elastic=False, price_change_percent=price_change_percent, volume_change_percent=0.0, model_trained=False)

        volume_change_percent = self.elasticity_coefficient * price_change_percent
        confidence = max(0.0, (self.r2 or 0)) * (1 - min(abs(price_change_percent) / 100, 0.5))
        return ElasticityResult(elasticity=self.elasticity_coefficient, confidence=confidence, r2_score=self.r2, mape=self.mape, is_elastic=abs(self.elasticity_coefficient) > 1, price_change_percent=price_change_percent, volume_change_percent=volume_change_percent, model_trained=True)

    def save(self, path: str) -> None:
        joblib.dump({"model": self.model, "scaler": self.scaler, "elasticity": self.elasticity_coefficient, "r2": self.r2, "mape": self.mape, "is_trained": self.is_trained}, path)
        logger.info("Модель сохранена: {}", path)

    def load(self, path: str) -> None:
        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.elasticity_coefficient = data["elasticity"]
        self.r2 = data["r2"]
        self.mape = data["mape"]
        self.is_trained = data["is_trained"]
        logger.info("Модель загружена: {}", path)
