from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class WorkflowStep(BaseModel):
    name: str
    event_type: str
    handler: str
    condition: str | None = None
    next_step: str | None = None
    timeout_seconds: int = 300


class Workflow(BaseModel):
    name: str
    description: str = ""
    steps: list[WorkflowStep] = []
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""
