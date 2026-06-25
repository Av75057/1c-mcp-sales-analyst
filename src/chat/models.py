from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatSession(BaseModel):
    id: str
    user_id: str
    title: str = "Новый чат"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_archived: bool = False
    messages_count: int = 0
    last_message_preview: str = ""


class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: str  # user, assistant, system
    content: str
    tokens_used: int | None = None
    response_time_ms: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ToolCall(BaseModel):
    id: str
    message_id: str
    tool_name: str
    arguments: dict[str, Any] | None = None
    result: str | None = None
    execution_time_ms: int | None = None
    status: str = "success"  # success, error
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
