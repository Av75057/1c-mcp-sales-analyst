from __future__ import annotations

import base64
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.logger import logger


class ChartFileManager:
    def __init__(self, charts_dir: str | Path = "./static/charts") -> None:
        self.charts_dir = Path(charts_dir)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def _date_dir(self) -> Path:
        d = self.charts_dir / datetime.now().strftime("%Y/%m/%d")
        d.mkdir(parents=True, exist_ok=True)
        return d

    def png_path(self, chart_id: str) -> Path:
        return self._date_dir() / f"{chart_id}.png"

    def html_path(self, chart_id: str) -> Path:
        return self._date_dir() / f"{chart_id}.html"

    def read_base64(self, path: Path) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def cleanup(self, days: int = 1) -> int:
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        count = 0
        for f in self.charts_dir.rglob("*"):
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                count += 1
        for d in sorted(self.charts_dir.rglob("*"), key=lambda p: len(str(p)), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        if count:
            logger.info("Очищено {} старых файлов графиков", count)
        return count
