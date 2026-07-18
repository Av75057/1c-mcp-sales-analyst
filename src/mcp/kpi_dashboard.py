from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field

import base64

import httpx

from src.cache import cache
from src.config import settings
from src.logger import logger
from src.metrics import metrics
from src.tools import get_client

PeriodType = Literal["today", "yesterday", "this_week", "last_week", "this_month", "last_month", "this_quarter", "this_year"]


class MetricData(BaseModel):
    current: float = 0.0
    previous: float = 0.0
    trend_percent: float = 0.0


class ExecutiveKPIResponse(BaseModel):
    period_label: str
    revenue: MetricData
    profit: MetricData
    orders_count: MetricData
    margin_percent: MetricData
    top_manager: dict = Field(default_factory=dict)
    sparklines: dict = Field(default_factory=dict)
    cache_status: str = "miss"


def calculate_trend(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / abs(previous)) * 100, 1)


_RU_MONTHS = ["", "янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
_RU_WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def _ru_date(d: datetime) -> str:
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def format_period_label(period: PeriodType, now: datetime | None = None) -> str:
    if now is None:
        now = datetime.now()
    labels = {
        "today": f"Сегодня, {_ru_date(now)}",
        "yesterday": f"Вчера, {_ru_date(now - timedelta(days=1))}",
        "this_week": f"Текущая неделя ({_ru_date(now - timedelta(days=now.weekday()))} — {_ru_date(now)})",
        "last_week": f"Прошлая неделя ({_ru_date(now - timedelta(days=now.weekday() + 7))} — {_ru_date(now - timedelta(days=now.weekday() + 1))})",
        "this_month": f"Текущий месяц, {_RU_MONTHS[now.month]} {now.year}",
        "last_month": f"Прошлый месяц, {_RU_MONTHS[(now.replace(day=1) - timedelta(days=1)).month]} {(now.replace(day=1) - timedelta(days=1)).year}",
        "this_quarter": f"Текущий квартал, {now.year}",
        "this_year": f"Текущий год, {now.year}",
    }
    return labels.get(period, period.replace("_", " ").title())


def get_period_boundaries(period: PeriodType, now: datetime | None = None) -> tuple[str, str, str, str, str]:
    if now is None:
        now = datetime.now()

    period_label = format_period_label(period, now)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "today":
        cur_start = today
        cur_end = today + timedelta(days=1) - timedelta(seconds=1)
        prev_start = cur_start - timedelta(days=1)
        prev_end = cur_end - timedelta(days=1)
    elif period == "yesterday":
        cur_start = today - timedelta(days=1)
        cur_end = today - timedelta(seconds=1)
        prev_start = cur_start - timedelta(days=1)
        prev_end = cur_end - timedelta(days=1)
    elif period == "this_week":
        cur_start = today - timedelta(days=today.weekday())
        cur_end = today + timedelta(days=6, hours=23, minutes=59, seconds=59)
        prev_start = cur_start - timedelta(days=7)
        prev_end = cur_end - timedelta(days=7)
    elif period == "last_week":
        cur_start = today - timedelta(days=today.weekday() + 7)
        cur_end = cur_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        prev_start = cur_start - timedelta(days=7)
        prev_end = cur_end - timedelta(days=7)
    elif period == "this_month":
        cur_start = today.replace(day=1)
        if today.month == 12:
            cur_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(seconds=1)
        else:
            cur_end = today.replace(month=today.month + 1, day=1) - timedelta(seconds=1)
        prev_start = cur_start.replace(day=1) - timedelta(days=1)
        prev_start = prev_start.replace(day=1)
        prev_end = cur_start - timedelta(seconds=1)
    elif period == "last_month":
        cur_start = today.replace(day=1) - timedelta(days=1)
        cur_start = cur_start.replace(day=1)
        if cur_start.month == 12:
            cur_end = cur_start.replace(year=cur_start.year + 1, month=1, day=1) - timedelta(seconds=1)
        else:
            cur_end = cur_start.replace(month=cur_start.month + 1, day=1) - timedelta(seconds=1)
        prev_start = cur_start.replace(day=1) - timedelta(days=1)
        prev_start = prev_start.replace(day=1)
        prev_end = cur_start - timedelta(seconds=1)
    elif period == "this_quarter":
        q = (today.month - 1) // 3
        cur_start = today.replace(month=q * 3 + 1, day=1)
        if q * 3 + 3 >= 12:
            cur_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(seconds=1)
        else:
            cur_end = today.replace(month=q * 3 + 4, day=1) - timedelta(seconds=1)
        prev_start = cur_start.replace(month=cur_start.month - 3, day=1)
        prev_end = cur_start - timedelta(seconds=1)
    elif period == "this_year":
        cur_start = today.replace(month=1, day=1)
        cur_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(seconds=1)
        prev_start = cur_start.replace(year=cur_start.year - 1, day=1)
        prev_end = cur_start - timedelta(seconds=1)
    else:
        raise ValueError(f"Unknown period: {period}")

    fmt = "%Y-%m-%dT%H:%M:%S"
    return (
        period_label,
        cur_start.strftime(fmt),
        cur_end.strftime(fmt),
        prev_start.strftime(fmt),
        prev_end.strftime(fmt),
    )


def _generate_mock_kpi(period_label: str, include_sparklines: bool) -> ExecutiveKPIResponse:
    import random
    rng = random.Random(42)

    rev_current = rng.uniform(800000, 2500000)
    rev_previous = rng.uniform(700000, 2300000)
    profit_current = rev_current * rng.uniform(0.18, 0.35)
    profit_previous = rev_previous * rng.uniform(0.18, 0.35)
    orders_current = rng.randint(15, 60)
    orders_previous = rng.randint(12, 55)
    margin_current = (profit_current / rev_current * 100) if rev_current else 0
    margin_previous = (profit_previous / rev_previous * 100) if rev_previous else 0

    sparklines_data = {}
    if include_sparklines:
        dates = []
        val = rev_current / 20
        for i in range(20):
            dates.append({"date": f"2026-07-{i+1:02d}", "value": round(val * (1 + rng.uniform(-0.15, 0.15)), 2)})
            val *= 1 + rng.uniform(-0.05, 0.08)
        sparklines_data["revenue"] = dates

    return ExecutiveKPIResponse(
        period_label=period_label,
        revenue=MetricData(
            current=round(rev_current, 2),
            previous=round(rev_previous, 2),
            trend_percent=calculate_trend(rev_current, rev_previous),
        ),
        profit=MetricData(
            current=round(profit_current, 2),
            previous=round(profit_previous, 2),
            trend_percent=calculate_trend(profit_current, profit_previous),
        ),
        orders_count=MetricData(
            current=orders_current,
            previous=orders_previous,
            trend_percent=calculate_trend(float(orders_current), float(orders_previous)),
        ),
        margin_percent=MetricData(
            current=round(margin_current, 1),
            previous=round(margin_previous, 1),
            trend_percent=calculate_trend(margin_current, margin_previous),
        ),
        top_manager={"name": "Иванов И.И.", "revenue": round(rev_current * rng.uniform(0.25, 0.4), 2)},
        sparklines=sparklines_data,
        cache_status="miss",
    )


def _build_cache_key(period: str, organization: str | None, include_sparklines: bool) -> str:
    raw = json.dumps({"period": period, "org": organization, "sp": include_sparklines}, sort_keys=True)
    return f"kpi:{hashlib.md5(raw.encode()).hexdigest()[:16]}"


def _get_ttl(period: PeriodType) -> int:
    if period in ("today", "yesterday"):
        return 300
    if period in ("this_week", "last_week"):
        return 900
    return 3600


async def get_executive_kpi(
    period: PeriodType,
    organization: str | None = None,
    include_sparklines: bool = True,
) -> ExecutiveKPIResponse:
    cache_key = _build_cache_key(period, organization, include_sparklines)
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("[KPI] Cache HIT: {}", cache_key)
        resp = ExecutiveKPIResponse(**cached)
        resp.cache_status = "hit"
        return resp

    logger.info("[KPI] Cache MISS: {}", cache_key)

    if settings.use_mock_data:
        period_label, *_ = get_period_boundaries(period)
        result = _generate_mock_kpi(period_label, include_sparklines)
    else:
        result = await _fetch_from_1c(period, organization, include_sparklines)

    cache.set(cache_key, result.model_dump(mode="json"), ttl=_get_ttl(period))
    return result


async def _fetch_profit_data(client: Any, d_from: str, d_to: str, pd_from: str, pd_to: str) -> tuple[float, float, float, float]:
    try:
        raw = f"{settings.c1_username}:{settings.c1_password}"
        auth = "Basic " + base64.b64encode(raw.encode("utf-8")).decode("ascii")
        base = settings.c1_base_url.rstrip("/")
        url = base.rstrip("/") + "/execute"

        def _dt(d: str) -> str:
            parts = d[:10].split("-")
            return f"ДАТАВРЕМЯ({parts[0]}, {int(parts[1])}, {int(parts[2])})"

        sql = (
            "ВЫБРАТЬ "
            "СУММА(Продажи.СуммаОборот) КАК Выручка, "
            "СУММА(Продажи.СебестоимостьОборот) КАК Себестоимость "
            "ИЗ РегистрНакопления.Продажи.Обороты(, {}, {}, , ) КАК Продажи"
        )

        async with httpx.AsyncClient(headers={"Authorization": auth, "Content-Type": "text/plain"}, timeout=15) as http:
            resp = await http.post(url, content=(sql.format(_dt(d_from), _dt(d_to))).encode("utf-8"))
            resp.raise_for_status()
            cur_data = resp.json()
            rev_c = float(cur_data.get("rows", [[0]])[0][0] if cur_data.get("rows") else 0)
            cost_c = float(cur_data.get("rows", [[0]])[0][1] if cur_data.get("rows") else 0)

            resp2 = await http.post(url, content=(sql.format(_dt(pd_from), _dt(pd_to))).encode("utf-8"))
            resp2.raise_for_status()
            prev_data = resp2.json()
            rev_p = float(prev_data.get("rows", [[0]])[0][0] if prev_data.get("rows") else 0)
            cost_p = float(prev_data.get("rows", [[0]])[0][1] if prev_data.get("rows") else 0)

        prof_c = round(rev_c - cost_c, 2)
        prof_p = round(rev_p - cost_p, 2)
        marg_c = round((prof_c / rev_c * 100) if rev_c else 0, 1)
        marg_p = round((prof_p / rev_p * 100) if rev_p else 0, 1)
        return prof_c, prof_p, marg_c, marg_p
    except Exception as e:
        logger.warning("[KPI] Profit fetch failed, using fallback 25%: {}", e)
        return 0.0, 0.0, 25.0, 25.0


async def _fetch_from_1c(
    period: PeriodType,
    organization: str | None,
    include_sparklines: bool,
) -> ExecutiveKPIResponse:
    period_label, cur_start, cur_end, prev_start, prev_end = get_period_boundaries(period)

    client = get_client()
    d_from = cur_start[:10]
    d_to = cur_end[:10]
    pd_from = prev_start[:10]
    pd_to = prev_end[:10]

    cur_sales, prev_sales, cur_managers = await asyncio.gather(
        client.get_sales(date_from=d_from, date_to=d_to, warehouse=organization, limit=50000),
        client.get_sales(date_from=pd_from, date_to=pd_to, warehouse=organization, limit=50000),
        client.get_sales_by_manager(date_from=d_from, date_to=d_to),
        return_exceptions=True,
    )

    def _safe_sales(data: Any) -> list[dict]:
        if isinstance(data, Exception):
            logger.error("[KPI] Error fetching sales: {}", data)
            return []
        return data or []

    cur_sales = _safe_sales(cur_sales)
    prev_sales = _safe_sales(prev_sales)
    cur_managers = _safe_sales(cur_managers)

    # Расчёт метрик (только строки с sum > 0 — товарные позиции)
    billed_c = [s for s in cur_sales if s.get("sum", 0) > 0]
    billed_p = [s for s in prev_sales if s.get("sum", 0) > 0]

    rev_c = sum(s.get("sum", 0) for s in billed_c)
    rev_p = sum(s.get("sum", 0) for s in billed_p)
    ord_c = len(billed_c)
    ord_p = len(billed_p)

    # Прибыль и маржа из регистра Продажи (себестоимость). Если не удалось — fallback 25%
    profit_c, profit_p, margin_c, margin_p = await _fetch_profit_data(client, d_from, d_to, pd_from, pd_to)
    if profit_c == 0 and rev_c > 0:
        profit_c = rev_c * 0.25
    if profit_p == 0 and rev_p > 0:
        profit_p = rev_p * 0.25
    if margin_c == 0 and rev_c > 0:
        margin_c = 25.0
    if margin_p == 0 and rev_p > 0:
        margin_p = 25.0

    # Топ-менеджер
    top_mgr = {"name": "", "revenue": 0}
    if cur_managers:
        best = max(cur_managers, key=lambda m: m.get("total_sum", 0))
        top_mgr = {"name": best.get("manager", ""), "revenue": best.get("total_sum", 0)}

    # Спарклайны (группировка по дням, с заполнением пропусков)
    sparklines = {}
    if include_sparklines and billed_c:
        daily: dict[str, float] = {}
        for s in billed_c:
            day = s.get("date", "")[:10]
            if day:
                daily[day] = daily.get(day, 0) + s.get("sum", 0)

        # Заполняем все дни периода нулями, где нет данных
        start_date = datetime.strptime(cur_start[:10], "%Y-%m-%d")
        end_date = datetime.strptime(cur_end[:10], "%Y-%m-%d")
        filled = []
        cur = start_date
        while cur <= end_date:
            ds = cur.strftime("%Y-%m-%d")
            filled.append({"date": ds, "value": round(daily.get(ds, 0), 2)})
            cur += timedelta(days=1)

        sparklines["revenue"] = filled

    return ExecutiveKPIResponse(
        period_label=period_label,
        revenue=MetricData(
            current=round(rev_c, 2), previous=round(rev_p, 2),
            trend_percent=calculate_trend(rev_c, rev_p),
        ),
        profit=MetricData(
            current=round(profit_c, 2), previous=round(profit_p, 2),
            trend_percent=calculate_trend(profit_c, profit_p),
        ),
        orders_count=MetricData(
            current=ord_c, previous=ord_p,
            trend_percent=calculate_trend(float(ord_c), float(ord_p)),
        ),
        margin_percent=MetricData(
            current=margin_c, previous=margin_p,
            trend_percent=calculate_trend(margin_c, margin_p),
        ),
        top_manager=top_mgr,
        sparklines=sparklines,
        cache_status="miss",
    )
