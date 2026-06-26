from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ClientRecord(BaseModel):
    id: str = ""
    name: str = Field(default="", min_length=2)
    inn: str | None = None
    type: str = "unknown"
    is_active: bool = True

    @field_validator("inn", mode="before")
    @classmethod
    def validate_inn(cls, v: object) -> object:
        if v and isinstance(v, str):
            if len(v) not in (10, 12) or not v.isdigit():
                raise ValueError("ИНН должен быть 10 или 12 цифр")
        return v
