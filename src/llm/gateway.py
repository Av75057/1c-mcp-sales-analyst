"""LLM Gateway - unified model interface."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from typing import Any

import httpx

from .models import FALLBACK_CHAINS, MODEL_ROUTING, LLMRequest, LLMResponse
from .models import Message, ModelConfig, TaskType, ToolCall
from .observability import LLMTrace, metrics
from .prompts import get_current_version, load_prompt

logger = logging.getLogger("llm.gateway")


class LLMGateway:
    def __init__(self, use_mock: bool | None = None, cache_ttl: int = 300) -> None:
        self._use_mock = use_mock if use_mock is not None else (
            os.getenv("USE_MOCK_DATA", "false") == "true"
        )
        self._cache: dict[str, tuple[float, LLMResponse]] = {}
        self._cache_ttl = cache_ttl
        self._lock = asyncio.Lock()
        self._openai_key = os.getenv("OPENAI_API_KEY", "")
        self._deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        self._openai_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self._deepseek_base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        config = MODEL_ROUTING.get(request.task, MODEL_ROUTING[TaskType.CHAT])
        cache_key = self._cache_key(request)
        cached = self._get_cached(cache_key)
        if cached:
            cached.cached = True
            self._trace(request, cached, config, cached=True)
            return cached

        chain = FALLBACK_CHAINS.get(config.provider, [config.provider, "mock"])
        last_error: str | None = None

        for provider in chain:
            if provider == "mock" or self._use_mock:
                response = self._mock_response(request, config)
                if last_error:
                    response.error = last_error
                self._trace(request, response, config)
                self._set_cached(cache_key, response)
                return response

            try:
                response = await self._call_provider(provider, request, config)
                self._trace(request, response, config,
                           fallback_used=(provider != config.provider))
                self._set_cached(cache_key, response)
                return response
            except Exception as e:
                last_error = f"{provider}: {e}"
                logger.warning("LLM fallback: %s -> next (%s)", provider, e)
                continue


    async def complete_with_prompt(
        self, task: TaskType, user_message: str,
        session_id: str | None = None, user_id: str | None = None,
        history: list[Message] | None = None, **kwargs: Any,
    ) -> LLMResponse:
        system_prompt = load_prompt(task.value)
        version = get_current_version(task.value)
        messages: list[Message] = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        if history:
            messages.extend(history)
        messages.append(Message(role="user", content=user_message))
        request = LLMRequest(
            task=task, messages=messages,
            session_id=session_id, user_id=user_id,
            metadata={"prompt_version": version, **kwargs},
        )
        return await self.complete(request)

    async def _call_provider(
        self, provider: str, request: LLMRequest, config: ModelConfig
    ) -> LLMResponse:
        if provider == "openai":
            base_url, api_key = self._openai_base, self._openai_key
        elif provider == "deepseek":
            base_url, api_key = self._deepseek_base, self._deepseek_key
        else:
            raise ValueError(f"Unknown provider: {provider}")
        if not api_key:
            raise ValueError(f"API key not set for {provider}")

        payload: dict[str, Any] = {
            "model": config.model,
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
            "max_tokens": request.max_tokens or config.max_tokens,
            "temperature": request.temperature,
        }
        if request.tools:
            payload["tools"] = [
                {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
                for t in request.tools
            ]
        if request.response_format:
            payload["response_format"] = request.response_format

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.monotonic() - start) * 1000
        choice = data["choices"][0]
        message = choice["message"]
        usage = data.get("usage", {})

        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        cost = tokens_in / 1000 * config.cost_per_1k_in + tokens_out / 1000 * config.cost_per_1k_out

        tool_calls = None
        if message.get("tool_calls"):
            tool_calls = [
                ToolCall(id=tc["id"], name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"]))
                for tc in message["tool_calls"]
            ]

        return LLMResponse(
            request_id=request.request_id,
            content=message.get("content") or "",
            tool_calls=tool_calls, model=config.model, provider=provider,
            tokens_in=tokens_in, tokens_out=tokens_out, cost=round(cost, 6),
            latency_ms=round(latency_ms, 1),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    def _mock_response(self, request: LLMRequest, config: ModelConfig) -> LLMResponse:
        mock_content = {
            TaskType.CHAT: "This is a mock AI analyst response.",
            TaskType.CLASSIFICATION: '{"category": "sales_query", "confidence": 0.95}',
            TaskType.INSIGHT: "Revenue grew by 12%.",
            TaskType.REFLECTION: "PASS",
            TaskType.SUMMARIZATION: "Summary content.",
            TaskType.EMBEDDING: "",
        }
        return LLMResponse(
            request_id=request.request_id,
            content=mock_content.get(request.task, "mock response"),
            model="mock", provider="mock",
            tokens_in=10, tokens_out=20, cost=0.0, latency_ms=1.0,
            finish_reason="stop",
        )

    def _cache_key(self, request: LLMRequest) -> str:
        raw = json.dumps(
            {"task": request.task.value, "messages": [m.content for m in request.messages], "temperature": request.temperature},
            ensure_ascii=False, sort_keys=True,
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _get_cached(self, key: str) -> LLMResponse | None:
        if key in self._cache:
            ts, response = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return response.model_copy()
            del self._cache[key]
        return None

    def _set_cached(self, key: str, response: LLMResponse) -> None:
        if response.error or response.tool_calls:
            return
        self._cache[key] = (time.time(), response.model_copy())
        if len(self._cache) > 500:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]

    def _trace(self, request: LLMRequest, response: LLMResponse,
               config: ModelConfig, cached: bool = False, fallback_used: bool = False) -> None:
        trace = LLMTrace(
            request_id=request.request_id, session_id=request.session_id,
            user_id=request.user_id, task=request.task.value,
            model=response.model, provider=response.provider,
            prompt_version=request.metadata.get("prompt_version", "inline"),
            tokens_in=response.tokens_in, tokens_out=response.tokens_out,
            cost=response.cost, latency_ms=response.latency_ms,
            tool_calls=[tc.name for tc in (response.tool_calls or [])],
            cached=cached, error=response.error, fallback_used=fallback_used,
        )
        trace.log()
        metrics.record(trace)


_gateway: LLMGateway | None = None


def get_gateway() -> LLMGateway:
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway
