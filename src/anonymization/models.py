from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SensitiveDataType(str, Enum):
    PERSON = "ПЕРС"
    ORGANIZATION = "ОРГ"
    CONTACT = "КОНТ"
    FINANCIAL = "ФИН"
    DOCUMENT = "ДОК"
    ADDRESS = "АДР"
    CUSTOM = "КАСТ"


ANONYMIZATION_RULES: dict[str, SensitiveDataType] = {
    "client_name": SensitiveDataType.PERSON,
    "client_inn": SensitiveDataType.DOCUMENT,
    "client_phone": SensitiveDataType.CONTACT,
    "client_email": SensitiveDataType.CONTACT,
    "client_address": SensitiveDataType.ADDRESS,
    "contact_person": SensitiveDataType.PERSON,
    "manager_name": SensitiveDataType.PERSON,
    "organization_name": SensitiveDataType.ORGANIZATION,
    "bank_account": SensitiveDataType.FINANCIAL,
}


class AnonymizationContext(BaseModel):
    user_id: str
    session_id: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    mapping: dict[str, str] = Field(default_factory=dict)

    def add_mapping(self, token: str, original: str, data_type: SensitiveDataType) -> None:
        self.mapping[token] = original
