from __future__ import annotations

import asyncio
from typing import Any

import httpx

from src.insights.models import ProcessedInsight
from src.logger import logger

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


class TelegramDelivery:
    def __init__(self, bot_token: str, chat_ids: list[str]) -> None:
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def send_insight(self, insight: ProcessedInsight) -> list[dict[str, Any]]:
        if not self.chat_ids or not self.bot_token:
            logger.info("Telegram не настроен (нет токена или chat_ids)")
            return []

        results: list[dict[str, Any]] = []
        text = insight.formatted_message or f"{insight.llm_title}\n\n{insight.llm_summary}"
        if len(text) > 4000:
            text = text[:3997] + "..."

        client = await self._get_client()

        for chat_id in self.chat_ids:
            try:
                resp = await client.post(
                    TELEGRAM_API.format(token=self.bot_token, method="sendMessage"),
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
                )
                result = resp.json()
                if result.get("ok"):
                    logger.info("Telegram: отправлено в {}", chat_id)
                    results.append({"chat_id": chat_id, "ok": True})
                else:
                    logger.error("Telegram error: {}", result)
                    results.append({"chat_id": chat_id, "ok": False, "error": result})
            except Exception as e:
                logger.error("Telegram send error: {}", e)
                results.append({"chat_id": chat_id, "ok": False, "error": str(e)})

        return results

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
