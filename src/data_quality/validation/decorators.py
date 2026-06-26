from __future__ import annotations

import functools
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from src.logger import logger


def validate_output(model_class: type[BaseModel]) -> Callable:
    """Декоратор для валидации выходных данных MCP tools."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)

            if isinstance(result, list):
                validated: list[dict] = []
                issues: list[dict] = []
                for item in result:
                    try:
                        validated.append(model_class(**item).model_dump())
                    except ValidationError as e:
                        issues.append({"record": str(item.get("id", item.get("nomenclature", "?"))), "errors": e.errors()})
                if issues:
                    logger.warning("[DataQuality] {}: {}/{} invalid", func.__name__, len(issues), len(result))
                return validated
            else:
                try:
                    return model_class(**result).model_dump()
                except ValidationError as e:
                    logger.error("[DataQuality] {} failed: {}", func.__name__, e.errors())
                    return result

        return wrapper
    return decorator
