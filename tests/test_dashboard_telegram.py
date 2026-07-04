from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from src.dashboard.bot.service import TelegramBot


class TestTelegramBot:
    def test_disabled_when_no_token(self):
        bot = TelegramBot()
        bot.token = ""
        bot.chat_id = ""
        assert bot._enabled is False

    def test_disabled_when_no_chat_id(self):
        bot = TelegramBot()
        bot.token = "test:token"
        bot.chat_id = ""
        assert bot._enabled is False

    def test_enabled(self):
        bot = TelegramBot()
        bot.token = "test:token"
        bot.chat_id = "12345"
        bot.api_url = f"https://api.telegram.org/bot{bot.token}"
        bot._enabled = True
        assert bot._enabled is True
        assert bot.api_url == "https://api.telegram.org/bottest:token"

    @pytest.mark.asyncio
    async def test_send_message_disabled(self):
        bot = TelegramBot()
        bot.token = ""
        result = await bot.send_message("test")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        bot = TelegramBot()
        bot.token = "test:token"
        bot.chat_id = "12345"
        bot._enabled = True

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await bot.send_message("<b>test</b>")
            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_dashboard_shared(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200
        with patch("httpx.AsyncClient", return_value=mock_client):
            await bot.notify_dashboard_shared("Sales", "alice", "bob")
            assert mock_client.post.called

    @pytest.mark.asyncio
    async def test_notify_report_ready(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200
        with patch("httpx.AsyncClient", return_value=mock_client):
            await bot.notify_report_ready("Sales", "csv")
            assert mock_client.post.called

    @pytest.mark.asyncio
    async def test_notify_anomaly(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200
        with patch("httpx.AsyncClient", return_value=mock_client):
            await bot.notify_anomaly("Sales", "Резкий спад")
            assert mock_client.post.called

    @pytest.mark.asyncio
    async def test_notify_recommendation(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200
        with patch("httpx.AsyncClient", return_value=mock_client):
            await bot.notify_recommendation("Sales", "Добавить график", 0.8)
            assert mock_client.post.called

    @pytest.mark.asyncio
    async def test_send_message_failure_status(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 400
        mock_client.post.return_value.text = "Bad Request"
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await bot.send_message("test")
            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_exception(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Connection error")
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await bot.send_message("test")
            assert result is False

    @pytest.mark.asyncio
    async def test_notify_dashboard_shared_content(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200
        with patch("httpx.AsyncClient", return_value=mock_client):
            await bot.notify_dashboard_shared("Мой дашборд", "alice", "bob")
            call_kwargs = mock_client.post.call_args[1]
            text = call_kwargs["json"]["text"]
            assert "Мой дашборд" in text
            assert "alice" in text
            assert "bob" in text
            assert text.startswith("🔐")

    @pytest.mark.asyncio
    async def test_notify_report_ready_content(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200
        with patch("httpx.AsyncClient", return_value=mock_client):
            await bot.notify_report_ready("Отчёт", "xlsx")
            call_kwargs = mock_client.post.call_args[1]
            text = call_kwargs["json"]["text"]
            assert "Отчёт" in text
            assert "xlsx" in text
            assert text.startswith("📊")

    @pytest.mark.asyncio
    async def test_notify_report_ready_uses_html(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200
        with patch("httpx.AsyncClient", return_value=mock_client):
            await bot.send_message("<b>bold</b> <i>italic</i>")
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["json"]["parse_mode"] == "HTML"
            assert "<b>bold</b>" in call_kwargs["json"]["text"]

    @pytest.mark.asyncio
    async def test_notify_anomaly_content(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200
        with patch("httpx.AsyncClient", return_value=mock_client):
            await bot.notify_anomaly("Sales dash", "Резкое падение продаж на 30%")
            call_kwargs = mock_client.post.call_args[1]
            text = call_kwargs["json"]["text"]
            assert "Sales dash" in text
            assert "30%" in text
            assert text.startswith("⚠️")

    @pytest.mark.asyncio
    async def test_notify_recommendation_content(self):
        bot = TelegramBot()
        bot.token = "t"
        bot.chat_id = "1"
        bot._enabled = True
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value.status_code = 200
        with patch("httpx.AsyncClient", return_value=mock_client):
            await bot.notify_recommendation("Sales", "Добавить график", 0.85)
            call_kwargs = mock_client.post.call_args[1]
            text = call_kwargs["json"]["text"]
            assert "85%" in text or "0.85" in text
            assert "Добавить график" in text
