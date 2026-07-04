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

    # Таймауты и retry
    c1_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("C1_TIMEOUT_SECONDS", "60"))
    )
    c1_connect_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("C1_CONNECT_TIMEOUT_SECONDS", "10"))
    )
    c1_max_retries: int = field(
        default_factory=lambda: int(os.getenv("C1_MAX_RETRIES", "3"))
    )
    c1_retry_delay_seconds: int = field(
        default_factory=lambda: int(os.getenv("C1_RETRY_DELAY_SECONDS", "5"))
    )

    # Batch
    c1_batch_max_requests: int = field(
        default_factory=lambda: int(os.getenv("C1_BATCH_MAX_REQUESTS", "10"))
    )
    c1_batch_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("C1_BATCH_TIMEOUT_SECONDS", "120"))
    )

    # Безопасность
    jwt_secret_key: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", "change-me-in-production-use-random-64-bytes!!")
    )
    allowed_origins: list[str] = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
    )
    auth_enabled: bool = field(
        default_factory=lambda: os.getenv("AUTH_ENABLED", "true").lower() == "true"
    )

    # Telegram
    telegram_bot_token: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
    )
    telegram_chat_id: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", "")
    )

    # Кэш
    cache_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "300"))
    )
    cache_max_size: int = field(
        default_factory=lambda: int(os.getenv("CACHE_MAX_SIZE", "1000"))
    )

    def reload(self) -> None:
        for field_name in self.__dataclass_fields__:
            env_name = field_name.upper()
            factory = self.__dataclass_fields__[field_name].default_factory
            if factory:
                setattr(self, field_name, factory())

    def validate(self) -> None:
        if not self.deepseek_api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY не задан. "
                "Создайте .env файл на основе .env.example и укажите ключ."
            )


settings = Settings()
