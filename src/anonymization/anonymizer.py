from __future__ import annotations

from typing import Any

from src.anonymization.models import ANONYMIZATION_RULES, AnonymizationContext, SensitiveDataType
from src.anonymization.storage import get_or_create_token, reveal_text


class DataAnonymizer:
    def __init__(self) -> None:
        self.rules = dict(ANONYMIZATION_RULES)

    def anonymize(self, data: list[dict[str, Any]] | dict[str, Any], user_id: str, session_id: str = "") -> tuple[list[dict[str, Any]] | dict[str, Any], AnonymizationContext]:
        context = AnonymizationContext(user_id=user_id, session_id=session_id)
        if isinstance(data, dict):
            return self._anonymize_single(data, context), context
        return [self._anonymize_single(row, context) for row in data], context

    def _anonymize_single(self, row: dict[str, Any], context: AnonymizationContext) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in row.items():
            if key in self.rules and value and isinstance(value, str):
                token = get_or_create_token(value, self.rules[key], context.user_id, context.session_id)
                result[key] = token
                context.add_mapping(token, value, self.rules[key])
            else:
                result[key] = value
        return result

    def reveal(self, text: str, user_id: str, session_id: str = "") -> str:
        return reveal_text(text, user_id, session_id)


anonymizer = DataAnonymizer()
