from __future__ import annotations

import sys

from loguru import logger as _logger

from src.config import settings

_logger.remove()

_logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>",
)

_logger.add(
    "logs/mcp_server.log",
    rotation="10 MB",
    retention=7,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
)

logger = _logger
