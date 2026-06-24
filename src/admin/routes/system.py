from __future__ import annotations

import platform
import sys
from pathlib import Path

from fastapi import APIRouter, Depends

from src.admin.dependencies import require_admin

router = APIRouter(prefix="/admin/system", tags=["admin"])


@router.get("/")
async def system_info(_=Depends(require_admin)):
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime = int(psutil.boot_time())
    except ImportError:
        cpu_percent = mem = disk = uptime = 0

    try:
        import subprocess

        git_commit = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent.parent.parent,
        ).stdout.strip()
    except Exception:
        git_commit = "unknown"

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "git_commit": git_commit,
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": getattr(mem, "percent", 0) if mem else 0,
        "disk_usage_percent": getattr(disk, "percent", 0) if disk else 0,
        "uptime_seconds": uptime,
    }
