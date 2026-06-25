from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    group: str | None = None
    item_type: str | None = None
    in_stock: bool | None = None
    price_min: float | None = None
    price_max: float | None = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    strategy: str = "hybrid"
    filters: SearchFilters = Field(default_factory=SearchFilters)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)


class SearchResultItem(BaseModel):
    id: str
    name: str
    article: str = ""
    barcode: str = ""
    group: str = ""
    item_type: str = ""
    price: float = 0.0
    stock_qty: float = 0.0
    score: float = 0.0
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class FacetGroup(BaseModel):
    name: str
    count: int


class PriceRange(BaseModel):
    min: float = 0.0
    max: float = 0.0
    avg: float = 0.0


class SearchResponse(BaseModel):
    results: list[SearchResultItem] = Field(default_factory=list)
    facets: dict[str, Any] = Field(default_factory=dict)
    total: int = 0
    page: int = 1
    pages: int = 0
    search_time_ms: float = 0.0
