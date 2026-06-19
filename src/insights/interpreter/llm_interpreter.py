from __future__ import annotations

import json
import re
from typing import Any

from openai import AsyncOpenAI
import httpx

from src.config import settings
from src.insights.interpreter.prompts import INSIGHT_PROMPT, DIGEST_PROMPT
from src.insights.models import RawInsight, ProcessedInsight
from src.logger import logger


class LLMInterpreter:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
            http_client=httpx.AsyncClient(timeout=30.0),
        )
        self.model = settings.llm_model

    async def interpret(self, raw: RawInsight) -> ProcessedInsight:
        logger.info("LLM интерпретирует: {} ({})", raw.title, raw.priority)
        prompt = INSIGHT_PROMPT.format(raw_json=json.dumps({
            "detector": raw.detector,
            "priority": raw.priority,
            "entity": {"type": raw.entity_type, "name": raw.entity_name},
            "metric": {
                "name": raw.metric_name,
                "current": raw.metric_value,
                "baseline": raw.metric_baseline,
                "delta_percent": raw.metric_delta_percent,
            },
            "period": {"from": raw.period_from.isoformat(), "to": raw.period_to.isoformat()},
            "context": raw.context,
        }, ensure_ascii=False, indent=2))

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000,
            )
            content = (response.choices[0].message.content or "").strip()
            import re
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
            if m:
                content = m.group(1).strip()
            data = json.loads(content)
        except Exception as e:
            logger.error("LLM interpreter error: {}", e)
            data = {
                "title": raw.title,
                "summary": f"Обнаружено изменение метрики {raw.metric_name}: {raw.metric_delta_percent:+.1f}%",
                "hypothesis": "Невозможно определить причину (ошибка LLM)",
                "recommendations": ["Проверить данные вручную"],
                "formatted_message": self._fallback_message(raw),
            }

        return ProcessedInsight(
            raw=raw,
            llm_title=data.get("title", raw.title),
            llm_summary=data.get("summary", ""),
            llm_hypothesis=data.get("hypothesis", ""),
            llm_recommendations=data.get("recommendations", []),
            formatted_message=data.get("formatted_message", self._fallback_message(raw)),
        )

    async def interpret_batch(self, raws: list[RawInsight]) -> list[ProcessedInsight]:
        results: list[ProcessedInsight] = []
        for raw in raws:
            processed = await self.interpret(raw)
            results.append(processed)
        return results

    def _fallback_message(self, raw: RawInsight) -> str:
        emoji = "🔴" if raw.priority == "critical" else "🟡" if raw.priority == "warning" else "ℹ️"
        return (
            f"{emoji} {raw.title}\n\n"
            f"**Метрика:** {raw.metric_name}\n"
            f"**Текущее:** {raw.metric_value:.1f}\n"
            f"**Базовое:** {raw.metric_baseline:.1f}\n"
            f"**Изменение:** {raw.metric_delta_percent:+.1f}%\n"
            f"**Период:** {raw.period_from} - {raw.period_to}\n"
        )
