from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    deepseek_api_key: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", "")
    )
    c1_base_url: str = field(
        default_factory=lambda: os.getenv("C1_BASE_URL", "http://localhost/1c/api")
    )
    c1_username: str = field(
        default_factory=lambda: os.getenv("C1_USERNAME", "service_user")
    )
    c1_password: str = field(
        default_factory=lambda: os.getenv("C1_PASSWORD", "service_password")
    )
    mcp_host: str = field(
        default_factory=lambda: os.getenv("MCP_HOST", "0.0.0.0")
    )
    mcp_port: int = field(
        default_factory=lambda: int(os.getenv("MCP_PORT", "8000"))
    )
    llm_model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "deepseek-chat")
    )
    llm_temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.1"))
    )
    llm_max_tokens: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "2000"))
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "DEBUG")
    )
    use_mock_data: bool = field(
        default_factory=lambda: os.getenv("USE_MOCK_DATA", "true").lower() == "true"
    )

    def validate(self) -> None:
        if not self.deepseek_api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY не задан. "
                "Создайте .env файл на основе .env.example и укажите ключ."
            )


settings = Settings()
