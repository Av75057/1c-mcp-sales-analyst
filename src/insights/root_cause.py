from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any

import httpx
from openai import AsyncOpenAI

from src.clients.c1_client import C1Client
from src.clients.mock_c1_client import MockC1Client
from src.config import settings
from src.logger import logger

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

    client = C1Client() if not settings.use_mock_data else MockC1Client()

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
        ctx["sales_recent"] = []

    return ctx
