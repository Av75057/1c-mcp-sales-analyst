from __future__ import annotations

import base64
import io
import json
import re
from typing import Any

import httpx
from openai import AsyncOpenAI

from src.config import settings
from src.docparser.recognition.prompts import INVOICE_PROMPT
from src.logger import logger


class VisionClient:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
            http_client=httpx.AsyncClient(timeout=60.0),
        )
        self.model = "deepseek-chat"

    async def recognize(self, image_bytes: bytes, prompt: str | None = None) -> dict[str, Any]:
        logger.info("VisionClient: распознавание документа")
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}, "detail": "high"},
                    {"type": "text", "text": prompt or INVOICE_PROMPT},
                ],
            }
        ]

        for model in ["deepseek-chat", "gpt-4o", "gpt-4o-mini"]:
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.05,
                    max_tokens=2000,
                )
                content = response.choices[0].message.content or ""
                result = self._parse_response(content)
                logger.info("VisionClient: {} распознано {} позиций, doc_type={}", model, len(result.get("items", [])), result.get("doc_type"))
                return result
            except Exception as e:
                logger.warning("VisionClient: {} не работает ({}), пробую следующую модель...", model, e)
                continue

        logger.error("VisionClient: все модели недоступны")
        return {"error": "No vision model available", "doc_type": "error", "items": [], "totals": {}, "confidence": 0.0}

    def _parse_response(self, content: str) -> dict[str, Any]:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if m:
            content = m.group(1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("VisionClient: невалидный JSON, возвращаю сырой текст")
            return {"doc_type": "free_form", "raw": content, "items": [], "totals": {}, "confidence": 0.0}
