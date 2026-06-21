from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIStatusError, RateLimitError

from src.deepseek_client import DeepSeekClient, DeepSeekError


@pytest.fixture
def client():
    return DeepSeekClient()


def _mock_completion(content: str = "Ответ", tool_calls: list | None = None, finish: str = "stop"):
    choice = MagicMock()
    choice.message.content = content
    choice.message.tool_calls = tool_calls
    choice.finish_reason = finish
    usage = MagicMock(prompt_tokens=100, completion_tokens=50)
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


@pytest.mark.asyncio
async def test_simple_chat(client):
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = _mock_completion("Привет! Чем помочь?")

        result = await client.process_query("Привет")
        assert "Привет" in result["answer"]


@pytest.mark.asyncio
async def test_function_calling(client):
    tc = MagicMock()
    tc.id = "call_123"
    tc.type = "function"
    tc.function.name = "get_stock"
    tc.function.arguments = '{"item": "Гвоздь"}'

    resp1 = _mock_completion(content=None, tool_calls=[tc], finish="tool_calls")
    resp2 = _mock_completion(content="На складе 150 шт")

    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = [resp1, resp2]

        result = await client.process_query("Сколько гвоздей?")
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "get_stock"


@pytest.mark.asyncio
async def test_rate_limit_retry(client):
    rate_err = RateLimitError(
        message="Rate limit",
        response=MagicMock(status_code=429),
        body=None,
    )
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = [rate_err, _mock_completion("Ответ после retry")]

        result = await client.process_query("Привет")
        assert mock_create.call_count >= 2
        assert "Ответ" in result["answer"]


@pytest.mark.asyncio
async def test_server_error_retry(client):
    err = APIStatusError(
        message="Server Error",
        response=MagicMock(status_code=500),
        body=None,
    )
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = [err, err, _mock_completion("Ответ после retry")]

        result = await client.process_query("Привет")
        assert mock_create.call_count == 3


@pytest.mark.asyncio
async def test_ping_success(client):
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = _mock_completion("test")
        assert await client.ping() is True


@pytest.mark.asyncio
async def test_ping_failure(client):
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("API error")
        assert await client.ping() is False


@pytest.mark.asyncio
async def test_usage_tracking(client):
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = _mock_completion("Ответ")

        result = await client.process_query("Привет")
        assert result["usage"]["prompt_tokens"] >= 0


@pytest.mark.asyncio
async def test_tool_with_special_chars(client):
    tc = MagicMock()
    tc.id = "call_1"
    tc.type = "function"
    tc.function.name = "create_chart"
    tc.function.arguments = '{"title": "Товар \\"Премиум\\""}'

    resp1 = _mock_completion(content=None, tool_calls=[tc], finish="tool_calls")
    resp2 = _mock_completion(content="График готов")

    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = [resp1, resp2]
        result = await client.process_query("Построй график")
        assert result["tool_calls"][0]["name"] == "create_chart"
        assert "Премиум" in result["tool_calls"][0]["args"].get("title", "")
