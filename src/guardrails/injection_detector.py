from __future__ import annotations

import re
from typing import Any

from src.logger import logger

SUSPICIOUS_PATTERNS = [
    r"игнорируй\s+(все\s+)?предыдущие\s+инструкции",
    r"ты\s+теперь\s+",
    r"новый\s+системный\s+промпт",
    r"system\s*:\s*",
    r"<\|im_start\|>",
    r"забудь\s+все",
    r"отвечай\s+только",
]


class PromptInjectionDetector:
    """Обнаруживает попытки prompt injection."""

    def detect(self, text: str) -> bool:
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("[Guardrail] Prompt injection detected: {} in {!r}", pattern, text[:100])
                return True
        return False


injection_detector = PromptInjectionDetector()
