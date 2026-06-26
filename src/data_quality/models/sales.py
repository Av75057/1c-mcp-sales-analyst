from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class SalesRecord(BaseModel):
    id: str | None = None
    date: str = ""
    nomenclature: str = Field(default="", min_length=1)
    quantity: float = Field(default=0, ge=0)
    sum: float = Field(default=0, ge=0)
    manager: str | None = None
    client: str | None = None
    warehouse: str | None = None

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v: object) -> str:
        if not v:
            return ""
        try:
            d = datetime.fromisoformat(str(v).replace("Z", "+00:00")) if isinstance(v, str) else v
            if hasattr(d, "year") and d.year < 2000:
                raise ValueError(f"Нереалистичная дата: {v}")
        except (ValueError, TypeError):
            raise ValueError(f"Неверный формат даты: {v}")
        return str(v)[:10]

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v: object) -> float:
        return max(0.0, float(v or 0))

    @field_validator("sum", mode="before")
    @classmethod
    def validate_sum(cls, v: object) -> float:
        return max(0.0, float(v or 0))
