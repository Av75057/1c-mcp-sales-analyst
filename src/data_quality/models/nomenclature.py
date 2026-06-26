from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class NomenclatureRecord(BaseModel):
    id: str = ""
    name: str = Field(default="", min_length=1)
    article: str | None = None
    barcode: str | None = None
    unit: str = "шт"
    item_type: str = "товар"

    @field_validator("barcode", mode="before")
    @classmethod
    def validate_barcode(cls, v: object) -> object:
        if v and isinstance(v, str):
            if not v.isdigit() or len(v) not in (8, 12, 13):
                raise ValueError("Неверный штрихкод")
        return v
