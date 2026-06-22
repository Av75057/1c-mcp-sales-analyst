from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score


def calc_metrics(y_true: list[float], y_pred: list[float]) -> dict[str, float]:
    yt = np.array(y_true)
    yp = np.array(y_pred)
    mape = float(mean_absolute_percentage_error(yt, yp)) * 100
    mae = float(mean_absolute_error(yt, yp))
    rmse = float(np.sqrt(((yt - yp) ** 2).mean()))
    r2 = float(r2_score(yt, yp))
    return {"mape": round(mape, 2), "rmse": round(rmse, 2), "mae": round(mae, 2), "r2": round(r2, 3)}
