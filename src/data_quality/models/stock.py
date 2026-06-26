from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StockRecord(BaseModel):
    nomenclature: str = Field(default="", min_length=1)
    warehouse: str = ""
    quantity: float = Field(default=0, ge=0)
    unit: str = "шт"

    @classmethod
    def validate_stock(cls, data: list[dict]) -> list[dict]:
        validated = []
        for item in data:
            try:
                r = cls(**item)
                validated.append(r.model_dump())
            except Exception:
                pass
        return validated
