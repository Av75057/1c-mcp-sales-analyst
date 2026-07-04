"""Telegram бот для уведомлений о дашбордах и отчётах."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from src.config import settings
from src.logger import logger


class TelegramBot:
    """Отправляет уведомления в Telegram о событиях дашбордов."""

    def __init__(self) -> None:
        self.token = settings.telegram_bot_token or ""
        self.chat_id = settings.telegram_chat_id or ""
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self._enabled = bool(self.token and self.chat_id)

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self._enabled:
            logger.debug("[Telegram] Бот не настроен: пропускаем")
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode},
                )
                if resp.status_code == 200:
                    logger.info("[Telegram] Сообщение отправлено")
                    return True
                logger.warning("[Telegram] Ошибка отправки: {} {}", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("[Telegram] Ошибка: {}", e)
            return False

    async def notify_dashboard_shared(self, dashboard_title: str, shared_by: str, target_user: str) -> None:
        text = (
            f"🔐 <b>Доступ к дашборду</b>\n"
            f"Пользователь <b>{shared_by}</b> открыл доступ к дашборду\n"
            f"«{dashboard_title}»\n"
            f"для <b>{target_user}</b>"
        )
        await self.send_message(text)

    async def notify_report_ready(self, dashboard_title: str, format: str) -> None:
        text = (
            f"📊 <b>Отчёт готов</b>\n"
            f"Дашборд «{dashboard_title}»\n"
            f"Формат: {format}\n"
            f"Сформирован и отправлен получателям."
        )
        await self.send_message(text)

    async def notify_anomaly(self, dashboard_title: str, description: str) -> None:
        text = (
            f"⚠️ <b>Аномалия в дашборде</b>\n"
            f"Дашборд: «{dashboard_title}»\n"
            f"Описание: {description}"
        )
        await self.send_message(text)

    async def notify_recommendation(self, dashboard_title: str, rec_title: str, confidence: float) -> None:
        text = (
            f"💡 <b>Новая рекомендация ИИ</b>\n"
            f"Дашборд: «{dashboard_title}»\n"
            f"Рекомендация: {rec_title}\n"
            f"Уверенность: {confidence:.0%}"
        )
        await self.send_message(text)


telegram_bot = TelegramBot()
