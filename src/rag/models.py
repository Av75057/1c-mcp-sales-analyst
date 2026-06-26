from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    id: str = ""
    title: str = Field(default="", min_length=1, max_length=200)
    content: str = Field(default="", min_length=1)
    document_type: str = "general"
    tags: list[str] = []
    created_at: str = ""
    created_by: str = "system"
    is_active: bool = True
    version: int = 1
