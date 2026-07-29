#!/usr/bin/env python3
"""Production Web UI — запуск: python run_web.py"""
from __future__ import annotations

import uvicorn

from src.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "web.app:app",
        host=settings.mcp_host,
        port=settings.mcp_port,
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level="info",
    )
