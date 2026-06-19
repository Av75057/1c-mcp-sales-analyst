from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from src.logger import logger


def _normalize(name: str) -> str:
    """Приводим название к стандартному виду для сравнения"""
    name = name.lower().strip()
    name = re.sub(r"[^a-zа-яё0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def _token_sort_ratio(a: str, b: str) -> float:
    """Сравнение с сортировкой токенов (для перестановок слов)"""
    a_tokens = sorted(_normalize(a).split())
    b_tokens = sorted(_normalize(b).split())
    return SequenceMatcher(None, " ".join(a_tokens), " ".join(b_tokens)).ratio()


def _partial_ratio(a: str, b: str) -> float:
    """Проверяем, содержится ли один текст в другом"""
    a_norm = _normalize(a)
    b_norm = _normalize(b)
    if len(a_norm) <= len(b_norm):
        short, long_text = a_norm, b_norm
    else:
        short, long_text = b_norm, a_norm
    if short in long_text:
        return 1.0
    return max(SequenceMatcher(None, short, long_text[i:i + len(short) + 5]).ratio()
               for i in range(max(1, len(long_text) - len(short))))


def match_nomenclature(
    raw_name: str,
    catalog: list[dict[str, str]],
    threshold: float = 0.75,
) -> dict[str, Any]:
    """
    Сопоставляет распознанное название с номенклатурой из 1С.
    catalog: [{"id": "...", "name": "..."}]
    """
    if not catalog:
        return {"id": None, "name": None, "confidence": 0.0, "alternatives": []}

    scored: list[tuple[float, int]] = []
    for i, item in enumerate(catalog):
        name = item.get("name", "")
        tsr = _token_sort_ratio(raw_name, name)
        pr = _partial_ratio(raw_name, name)
        score = max(tsr, pr)
        scored.append((score, i))

    scored.sort(key=lambda x: -x[0])

    best_score, best_idx = scored[0][0], scored[0][1]
    best = catalog[best_idx]

    alternatives = [
        {"id": catalog[idx]["id"], "name": catalog[idx]["name"], "confidence": round(score, 2)}
        for score, idx in scored[1:4] if score > threshold - 0.2
    ]

    result: dict[str, Any] = {
        "id": best["id"] if best_score >= threshold else None,
        "name": best["name"] if best_score >= threshold else best["name"],
        "confidence": round(best_score, 2),
        "alternatives": alternatives,
    }
    logger.debug("nom_match: '{}' → '{}' ({:.2f})", raw_name, result["name"], best_score)
    return result


def match_counterparty(raw_name: str, catalog: list[dict[str, str]], threshold: float = 0.7) -> dict[str, Any]:
    return match_nomenclature(raw_name, catalog, threshold)
