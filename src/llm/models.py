"""Contracts for LLM Gateway."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    CHAT = "chat"
    CLASSIFICATION = "classification"
    INSIGHT = "insight"
    REFLECTION = "reflection"
    EMBEDDING = "embedding"
    SUMMARIZATION = "summarization"


class Message(BaseModel):
    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class LLMRequest(BaseModel):
    task: TaskType
    messages: list[Message]
    tools: list[ToolSchema] | None = None
    max_tokens: int = 2048
    temperature: float = 0.7
    response_format: dict | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str | None = None
    user_id: str | None = None


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class LLMResponse(BaseModel):
    request_id: str
    content: str
    tool_calls: list[ToolCall] | None = None
    model: str
    provider: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    cached: bool = False
    finish_reason: str = "stop"
    error: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.tokens_in + self.tokens_out


class ModelConfig(BaseModel):
    provider: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7
    cost_per_1k_in: float = 0.0
    cost_per_1k_out: float = 0.0
    timeout: float = 30.0
    max_retries: int = 2


MODEL_ROUTING: dict[TaskType, ModelConfig] = {
    TaskType.CLASSIFICATION: ModelConfig(
        provider="deepseek", model="deepseek-v4-flash", max_tokens=256,
        temperature=0.0, cost_per_1k_in=0.00007, cost_per_1k_out=0.00007,
    ),
    TaskType.CHAT: ModelConfig(
        provider="deepseek", model="deepseek-v4-flash", max_tokens=2048,
        temperature=0.7, cost_per_1k_in=0.00007, cost_per_1k_out=0.00007,
    ),
    TaskType.INSIGHT: ModelConfig(
        provider="deepseek", model="deepseek-v4-flash", max_tokens=4096,
        temperature=0.3, cost_per_1k_in=0.00007, cost_per_1k_out=0.00007,
    ),
    TaskType.REFLECTION: ModelConfig(
        provider="deepseek", model="deepseek-v4-flash", max_tokens=1024,
        temperature=0.2, cost_per_1k_in=0.00007, cost_per_1k_out=0.00007,
    ),
    TaskType.SUMMARIZATION: ModelConfig(
        provider="deepseek", model="deepseek-v4-flash", max_tokens=1024,
        temperature=0.3, cost_per_1k_in=0.00007, cost_per_1k_out=0.00007,
    ),
    TaskType.EMBEDDING: ModelConfig(
        provider="deepseek", model="deepseek-v4-flash", max_tokens=0,
        temperature=0.0, cost_per_1k_in=0.00007, cost_per_1k_out=0.00007,
    ),
}

FALLBACK_CHAINS: dict[str, list[str]] = {
    "openai": ["openai", "deepseek", "mock"],
    "deepseek": ["deepseek", "openai", "mock"],
}
