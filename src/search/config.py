from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchConfig:
    default_strategy: str = "hybrid"

    weights: dict[str, float] = field(default_factory=lambda: {"fts": 0.5, "semantic": 0.3, "popularity": 0.2})

    fuzzy_threshold: int = 80
    max_results_per_page: int = 50
    max_query_length: int = 200
    cache_enabled: bool = True
    cache_max_size: int = 1000
    cache_ttl_seconds: int = 300

    field_weights: dict[str, float] = field(default_factory=lambda: {"name": 10.0, "article": 8.0, "barcode": 10.0, "code": 5.0, "description": 3.0})


SEARCH_CONFIG = SearchConfig()
