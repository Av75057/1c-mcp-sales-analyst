from __future__ import annotations

from typing import Any

import pandas as pd

from src.forecasting.models import HoltWintersModel, LinearModel, ProphetModel, auto_select
from src.forecasting.metrics import calc_metrics
from src.logger import logger


def prepare_sales_data(sales: list[dict[str, Any]], item_name: str) -> pd.DataFrame:
    df = pd.DataFrame(sales)
    if df.empty:
        return df
    name_col = "nomenclature" if "nomenclature" in df.columns else "item"
    df = df[df[name_col].str.contains(item_name, case=False, na=False)].copy()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df.groupby("date")["quantity"].sum().reset_index()
    df.columns = ["date", "quantity"]
    return df.sort_values("date").reset_index(drop=True)


async def forecast_sales_tool(nomenclature: str, days: int = 30, method: str = "auto") -> dict[str, Any]:
    logger.info("forecast_sales: {} | {} дней | метод={}", nomenclature, days, method)

    from src.tools import get_client
    client = get_client()
    sales = await client.get_sales()

    df = prepare_sales_data(sales, nomenclature)
    if len(df) < 3:
        return {"error": f"Недостаточно данных для прогноза '{nomenclature}'. Нужно минимум 3 записи, найдено {len(df)}"}

    models = {"prophet": ProphetModel, "holt_winters": HoltWintersModel, "linear": LinearModel}
    if method == "auto":
        model = auto_select(df)
    elif method in models:
        model = models[method]()
    else:
        return {"error": f"Неизвестный метод: {method}. Допустимые: auto, prophet, holt_winters, linear"}

    train = df[:-7] if len(df) > 14 else df
    test = df[-7:] if len(df) > 14 else pd.DataFrame()
    model.fit(train)

    forecast_df = model.predict(days)
    if forecast_df.empty:
        return {"error": "Ошибка прогнозирования"}

    daily = forecast_df[["ds", "yhat", "yhat_lower", "yhat_upper"]].head(days).to_dict("records")
    formatted = [{"date": str(r["ds"].date() if hasattr(r["ds"], "date") else r["ds"]), "value": round(r["yhat"], 1), "lower_bound": round(r["yhat_lower"], 1), "upper_bound": round(r["yhat_upper"], 1)} for r in daily]

    total = sum(r["value"] for r in formatted)

    result: dict[str, Any] = {
        "item": {"name": nomenclature},
        "forecast_period": {"days": days},
        "method_used": {"name": model.name},
        "forecast": {"total": round(total, 0), "daily": formatted},
        "insights": [],
    }

    if not test.empty:
        pred = model.predict(len(test))
        if not pred.empty:
            y_true = test["quantity"].tolist()
            y_pred = [pred.iloc[i]["yhat"] for i in range(len(pred))]
            result["method_used"]["accuracy_metrics"] = calc_metrics(y_true, y_pred)

    return result


async def compare_forecasts_tool(nomenclature: str, test_days: int = 14) -> dict[str, Any]:
    logger.info("compare_forecasts: {} | test_days={}", nomenclature, test_days)

    from src.tools import get_client
    client = get_client()
    sales = await client.get_sales()

    df = prepare_sales_data(sales, nomenclature)
    if len(df) < test_days + 2:
        return {"error": f"Недостаточно данных. Нужно минимум {test_days + 7} записей, найдено {len(df)}"}

    train = df[:-test_days]
    test = df[-test_days:]
    y_true = test["quantity"].tolist()

    results: list[dict[str, Any]] = []
    models_to_test = [("Linear", LinearModel()), ("Holt-Winters", HoltWintersModel()), ("Prophet", ProphetModel())]

    for name, model in models_to_test:
        try:
            model.fit(train)
            pred = model.predict(test_days)
            if pred.empty:
                continue
            y_pred = [pred.iloc[i]["yhat"] for i in range(len(pred))]
            metrics = calc_metrics(y_true, y_pred)
            results.append({"method": name, **metrics})
        except Exception as e:
            logger.warning("{} failed: {}", name, e)

    if not results:
        return {"error": "Ни один метод не смог выполнить прогноз"}

    results.sort(key=lambda r: r["mape"])
    for i, r in enumerate(results):
        r["rank"] = i + 1

    best = results[0]
    return {
        "item": {"name": nomenclature},
        "test_period": {"test_days": test_days},
        "comparison": results,
        "recommendation": {"best_method": best["method"], "reason": f"Наименьшая ошибка MAPE ({best['mape']}%)", "expected_accuracy": f"±{best['mape']}% на горизонте {test_days} дней"},
    }


async def forecast_stockout_tool(
    lead_time_days: int = 7, safety_stock_days: int = 3, days_horizon: int = 60
) -> dict[str, Any]:
    from src.forecasting.stockout import predict_stockout
    from src.tools import get_client
    client = get_client()
    stock, sales = await client.get_stock(), await client.get_sales()
    return await predict_stockout(stock, sales, lead_time_days=lead_time_days, safety_stock_days=safety_stock_days, days_horizon=days_horizon)
