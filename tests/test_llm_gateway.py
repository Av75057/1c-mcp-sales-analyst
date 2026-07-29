"""Tests for LLM Gateway."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.llm import LLMGateway, LLMRequest, LLMResponse, Message, TaskType, metrics


@pytest.fixture
def gateway():
    return LLMGateway(use_mock=True)


@pytest.fixture
def sample_request():
    return LLMRequest(
        task=TaskType.CHAT,
        messages=[
            Message(role="system", content="You are an analyst."),
            Message(role="user", content="What is the revenue?"),
        ],
        session_id="test-session",
        user_id="test-user",
    )


@pytest.mark.asyncio
async def test_mock_response(gateway, sample_request):
    response = await gateway.complete(sample_request)
    assert response.provider == "mock"
    assert response.model == "mock"
    assert response.content
    assert response.cost == 0.0
    assert response.error is None


@pytest.mark.asyncio
async def test_mock_classification(gateway):
    request = LLMRequest(
        task=TaskType.CLASSIFICATION,
        messages=[Message(role="user", content="Show sales")],
    )
    response = await gateway.complete(request)
    assert "sales_query" in response.content


@pytest.mark.asyncio
async def test_cache_hit(gateway, sample_request):
    r1 = await gateway.complete(sample_request)
    assert not r1.cached

    r2 = await gateway.complete(sample_request)
    assert r2.cached
    assert r2.content == r1.content


@pytest.mark.asyncio
async def test_cache_miss_different_prompt(gateway):
    req1 = LLMRequest(
        task=TaskType.CHAT,
        messages=[Message(role="user", content="Question 1")],
    )
    req2 = LLMRequest(
        task=TaskType.CHAT,
        messages=[Message(role="user", content="Question 2")],
    )
    r1 = await gateway.complete(req1)
    r2 = await gateway.complete(req2)
    assert not r2.cached


@pytest.mark.asyncio
async def test_task_routing(gateway):
    for task in TaskType:
        request = LLMRequest(
            task=task,
            messages=[Message(role="user", content="test")],
        )
        response = await gateway.complete(request)
        assert response.model == "mock"


@pytest.mark.asyncio
async def test_fallback_to_mock():
    gw = LLMGateway(use_mock=False)
    gw._openai_key = "invalid-key"
    gw._deepseek_key = ""

    request = LLMRequest(
        task=TaskType.CHAT,
        messages=[Message(role="user", content="test")],
    )

    with patch("httpx.AsyncClient.post", side_effect=Exception("API error")):
        response = await gw.complete(request)

    assert response.provider == "mock"
    assert response.error is not None


@pytest.mark.asyncio
async def test_complete_with_prompt(gateway):
    response = await gateway.complete_with_prompt(
        task=TaskType.INSIGHT,
        user_message="Analyze sales",
        session_id="s1",
        user_id="u1",
    )
    assert response.content
    assert response.provider == "mock"


@pytest.mark.asyncio
async def test_metrics_recorded(gateway, sample_request):
    before = metrics.snapshot()["total_calls"]
    await gateway.complete(sample_request)
    after = metrics.snapshot()["total_calls"]
    assert after == before + 1


def test_request_validation():
    request = LLMRequest(
        task=TaskType.CHAT,
        messages=[Message(role="user", content="test")],
    )
    assert request.request_id
    assert request.max_tokens == 2048
    assert request.temperature == 0.7


def test_response_properties():
    response = LLMResponse(
        request_id="abc", content="test",
        model="gpt-4o", provider="openai",
        tokens_in=100, tokens_out=50,
    )
    assert response.total_tokens == 150
