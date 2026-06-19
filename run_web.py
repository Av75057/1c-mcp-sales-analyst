#!/usr/bin/env python3
"""Production Web UI — запуск: python run_web.py"""
from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True)
