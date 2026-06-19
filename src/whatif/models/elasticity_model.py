from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from src.logger import logger

MODEL_CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "models_cache"


class ElasticityModel:
    def __init__(self) -> None:
        self.model: Ridge | None = None
        self.scaler: StandardScaler | None = None
        self.elasticity: float = -0.5
        self.r2_score: float = 0.0
        MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, entity_id: str) -> Path:
        safe = entity_id.replace("/", "_").replace(" ", "_")
        return MODEL_CACHE_DIR / f"elasticity_{safe}.pkl"

    def is_trained(self, entity_id: str) -> bool:
        return self._cache_path(entity_id).exists()

    def train(self, sales_history: list[dict[str, Any]], entity_id: str = "default") -> None:
        prices: list[float] = []
        volumes: list[float] = []

        for s in sales_history:
            qty = s.get("quantity", 0)
            total = s.get("sum", 0)
            if qty > 0 and total > 0:
                prices.append(total / qty)
                volumes.append(qty)

        if len(prices) < 5:
            logger.warning("ElasticityModel: недостаточно данных для обучения ({} точек)", len(prices))
            self.elasticity = -0.5
            self.r2_score = 0.0
            return

        X = np.array(prices).reshape(-1, 1)
        y = np.array(volumes)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = Ridge(alpha=1.0)
        self.model.fit(X_scaled, y)

        self.r2_score = float(self.model.score(X_scaled, y))
        self.elasticity = float(self.model.coef_[0] * (np.mean(prices) / np.mean(volumes)))

        logger.info("ElasticityModel: обучена, E={:.3f}, R²={:.3f}, точек={}", self.elasticity, self.r2_score, len(prices))

        path = self._cache_path(entity_id)
        with open(path, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler, "elasticity": self.elasticity, "r2": self.r2_score}, f)

    def load(self, entity_id: str = "default") -> bool:
        path = self._cache_path(entity_id)
        if not path.exists():
            return False
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.model = data["model"]
            self.scaler = data["scaler"]
            self.elasticity = data["elasticity"]
            self.r2_score = data.get("r2", 0.0)
            return True
        except Exception as e:
            logger.error("ElasticityModel: ошибка загрузки: {}", e)
            return False

    def predict_volume_change(self, price_change_percent: float) -> float:
        volume_change = self.elasticity * price_change_percent
        return volume_change / 100.0

    def predict(self, price_change_percent: float, current_volume: float, current_price: float) -> dict[str, float]:
        volume_change_pct = self.predict_volume_change(price_change_percent)
        new_volume = current_volume * (1 + volume_change_pct)
        new_price = current_price * (1 + price_change_percent / 100.0)
        new_revenue = new_volume * new_price
        old_revenue = current_volume * current_price

        return {
            "elasticity": round(self.elasticity, 3),
            "volume_change_percent": round(volume_change_pct * 100, 1),
            "new_volume": round(new_volume, 0),
            "new_price": round(new_price, 2),
            "new_revenue": round(new_revenue, 2),
            "old_revenue": round(old_revenue, 2),
            "revenue_change_percent": round((new_revenue / old_revenue - 1) * 100, 1),
            "r2_score": round(self.r2_score, 3),
        }
