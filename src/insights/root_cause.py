from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any

import httpx
from openai import AsyncOpenAI

from src.config import settings
from src.logger import logger
from src.tools import get_client

ROOT_CAUSE_PROMPT = """Ты — аналитик, который объясняет причины аномалий в данных 1С.

АНОМАЛИЯ:
{anomaly}

КОНТЕКСТ:
{context}

ЗАДАЧА:
1. Определи ИСТИННУЮ причину аномалии, используя контекстные данные
2. Объясни простым языком (2-4 предложения)
3. Дай 1-2 конкретные рекомендации

ФОРМАТ ОТВЕТА (JSON):
{{"root_cause": "string",
  "explanation": "string",
  "confidence": 0.0,
  "recommendations": ["string"],
  "factors": ["string"]}}

ПРАВИЛА:
- Не выдумывай данные, которых нет в контексте
- Если причина неясна — confidence < 0.5
- Рекомендации должны быть конкретными и выполнимыми
- Пиши на русском языке"""


async def analyze_root_cause(anomaly: dict[str, Any]) -> dict[str, Any]:
    logger.info("Root cause analysis: {}", anomaly.get("title", ""))

    context = await _gather_context(anomaly)
    anomaly_text = json.dumps(anomaly, ensure_ascii=False, indent=2)
    context_text = json.dumps(context, ensure_ascii=False, indent=2)
    prompt = ROOT_CAUSE_PROMPT.format(anomaly=anomaly_text, context=context_text)

    try:
        client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url="https://api.deepseek.com", http_client=httpx.AsyncClient(timeout=30.0))
        resp = await client.chat.completions.create(model=settings.llm_model, messages=[{"role": "user", "content": prompt}], temperature=0.1, max_tokens=500)
        content = resp.choices[0].message.content or "{}"
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if m:
            content = m.group(1).strip()
        data = json.loads(content)
        data["anomaly_title"] = anomaly.get("title", "")
        return data
    except Exception as e:
        logger.error("Root cause analysis error: {}", e)
        return {"root_cause": "Не удалось определить причину", "explanation": f"Ошибка анализа: {e}", "confidence": 0.0, "recommendations": ["Проверьте данные вручную"], "factors": []}


async def _gather_context(anomaly: dict[str, Any]) -> dict[str, Any]:
    ctx: dict[str, Any] = {"anomaly_type": anomaly.get("detector", ""), "entity": anomaly.get("entity_id", ""), "detected_at": str(anomaly.get("detected_at", "")), "metric": anomaly.get("metric_name", ""), "delta": anomaly.get("metric_delta_percent", 0)}

    client = get_client()

    entity_name = anomaly.get("entity_id", anomaly.get("entity_name", ""))
    today = date.today()

    try:
        stock = await client.get_stock(nomenclature=entity_name)
        ctx["stock"] = [{"name": s.get("nomenclature", s.get("item", "")), "qty": s.get("quantity", 0)} for s in stock[:5]]
    except Exception:
        ctx["stock"] = []

    try:
        sales_recent = await client.get_sales(date_from=(today - timedelta(days=7)).isoformat(), date_to=today.isoformat())
        sales_prev = await client.get_sales(date_from=(today - timedelta(days=14)).isoformat(), date_to=(today - timedelta(days=7)).isoformat())
        ctx["sales_last_7d"] = sum(s.get("quantity", 0) for s in sales_recent)
        ctx["sales_prev_7d"] = sum(s.get("quantity", 0) for s in sales_prev)
        if entity_name:
            ctx["sales_item_recent"] = [s for s in sales_recent if entity_name.lower() in (s.get("nomenclature", "") or "").lower()][:5]
    except Exception:
        pass

    try:
        price_history = await client.get_price_history(item=entity_name, limit=5)
        ctx["price_history"] = [{"date": p.get("date", ""), "price": p.get("price", 0), "change": p.get("change_percent", 0)} for p in price_history[:5]]
    except Exception:
        ctx["price_history"] = []

    try:
        orders = await client.get_purchase_orders(item=entity_name)
        ctx["purchase_orders"] = [{"expected_date": o.get("expected_date", ""), "quantity": o.get("quantity", 0), "days_overdue": o.get("days_overdue", 0), "supplier": o.get("supplier", "")} for o in orders[:5]]
    except Exception:
        ctx["purchase_orders"] = []

    try:
        movement = await client.get_item_movement(item=entity_name, date_from=(today - timedelta(days=14)).isoformat(), date_to=today.isoformat())
        ctx["item_movement"] = [{"date": m.get("date", ""), "incoming": m.get("incoming", 0), "outgoing": m.get("outgoing", 0)} for m in movement[:20]]
    except Exception:
        ctx["item_movement"] = []

    return ctx
