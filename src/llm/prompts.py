"""Prompt versioning."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("llm.prompts")

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def load_prompt(task: str, version: str = "latest") -> str:
    task_dir = PROMPTS_DIR / task
    if not task_dir.exists():
        logger.warning("Prompt directory not found: %s", task_dir)
        return ""

    if version == "latest":
        files = sorted(task_dir.glob("v*.txt"))
        if not files:
            return ""
        path = files[-1]
    else:
        path = task_dir / f"{version}.txt"

    if not path.exists():
        logger.warning("Prompt not found: %s", path)
        return ""

    text = path.read_text(encoding="utf-8").strip()
    logger.debug("Loaded prompt: %s (%d chars)", path.name, len(text))
    return text


def list_versions(task: str) -> list[str]:
    task_dir = PROMPTS_DIR / task
    if not task_dir.exists():
        return []
    return sorted(f.stem for f in task_dir.glob("v*.txt"))


def get_current_version(task: str) -> str:
    versions = list_versions(task)
    return versions[-1] if versions else "none"
