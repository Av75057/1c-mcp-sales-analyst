from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SYNONYMS_FILE = Path(__file__).resolve().parent / "synonyms.json"


def _load() -> dict[str, list[str]]:
    if not SYNONYMS_FILE.exists():
        _save_defaults()
    try:
        return json.loads(SYNONYMS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict[str, list[str]]) -> None:
    SYNONYMS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _save_defaults() -> None:
    _save({
        "ноут": ["ноутбук", "лэптоп", "laptop"],
        "телефон": ["смартфон", "мобильник", "сотовый"],
        "комп": ["компьютер", "пк", "pc"],
        "принтер": ["мфу", "печатающее устройство"],
        "бумага": ["офсет", "мелованная", "картон"],
        "яблоко": ["apple", "фрукт"],
        "молоко": ["молочка", "молочный"],
        "хлеб": ["булка", "хлебобулочный"],
    })


def expand_query(query: str) -> list[str]:
    """Расширяет запрос синонимами."""
    data = _load()
    words = query.lower().split()
    expanded = [query]
    for word in words:
        if word in data:
            for synonym in data[word]:
                replaced = query.lower().replace(word, synonym, 1)
                if replaced != query.lower():
                    expanded.append(replaced)
    return expanded


def get_all() -> dict[str, Any]:
    return _load()


def add(word: str, synonyms: list[str]) -> None:
    data = _load()
    data[word.lower()] = synonyms
    _save(data)


def remove(word: str) -> None:
    data = _load()
    data.pop(word.lower(), None)
    _save(data)
