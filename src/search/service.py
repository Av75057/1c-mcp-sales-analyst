from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

from src.logger import logger
from src.search.cache import search_cache
from src.search.config import SEARCH_CONFIG
from src.search.models import SearchRequest, SearchResponse, SearchResultItem
from src.search.synonyms import expand_query


def multiword_score(query: str, item: dict[str, Any], field_weights: dict[str, float] | None = None) -> float:
    """Мультисловный поиск с весами полей."""
    if field_weights is None:
        field_weights = SEARCH_CONFIG.field_weights
    words = query.lower().split()
    score = 0.0

    for word in words:
        for field_name, weight in field_weights.items():
            field_value = str(item.get(field_name, "")).lower()
            if not field_value:
                continue
            words_in_field = field_value.split()
            if word in words_in_field:
                score += 10 * weight
            elif any(w.startswith(word) for w in words_in_field):
                score += 5 * weight
            elif word in field_value:
                score += 3 * weight
    return score


def fuzzy_score(query: str, item: dict[str, Any], threshold: int = 80) -> float:
    """Нечёткий поиск через rapidfuzz."""
    try:
        from rapidfuzz import fuzz
    except ImportError:
        return 0.0

    name = str(item.get("name", ""))
    desc = str(item.get("description", ""))
    best = 0.0
    for field in (name, desc):
        if not field:
            continue
        ratio = fuzz.WRatio(query.lower(), field.lower()) / 100.0
        if ratio > best:
            best = ratio
    return best if best * 100 >= threshold else 0.0


def compute_popularity_score(item: dict[str, Any]) -> float:
    sales = item.get("sales_30d", 0)
    return min(sales / 1000.0, 1.0)


def calculate_score(item: dict[str, Any], query: str) -> dict[str, float]:
    mw = multiword_score(query, item)
    fz = fuzzy_score(query, item)
    pop = compute_popularity_score(item)
    w = SEARCH_CONFIG.weights
    total = w["fts"] * mw / 100.0 + w["semantic"] * fz + w["popularity"] * pop
    return {"total": total, "multiword": mw, "fuzzy": fz, "popularity": pop}


def apply_filters(items: list[dict[str, Any]], filters: Any) -> list[dict[str, Any]]:
    if not filters:
        return items
    result = items
    if filters.group:
        fg = filters.group.lower()
        result = [i for i in result if fg in str(i.get("group", "")).lower()]
    if filters.item_type:
        t = filters.item_type.lower()
        result = [i for i in result if t in str(i.get("item_type", "")).lower()]
    if filters.in_stock is not None:
        result = [i for i in result if (i.get("stock_qty", 0) > 0) == filters.in_stock]
    if filters.price_min is not None:
        result = [i for i in result if i.get("price", 0) >= filters.price_min]
    if filters.price_max is not None:
        result = [i for i in result if i.get("price", 0) <= filters.price_max]
    return result


def compute_facets(items: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, int] = {}
    types: dict[str, int] = {}
    prices = []
    in_stock = 0
    for item in items:
        g = str(item.get("group", "") or "")
        if g:
            groups[g] = groups.get(g, 0) + 1
        t = str(item.get("item_type", "") or "")
        if t:
            types[t] = types.get(t, 0) + 1
        p = item.get("price", 0)
        if p:
            prices.append(p)
        if item.get("stock_qty", 0) > 0:
            in_stock += 1
    return {
        "groups": [{"name": k, "count": v} for k, v in sorted(groups.items(), key=lambda x: -x[1])[:10]],
        "types": [{"name": k, "count": v} for k, v in sorted(types.items(), key=lambda x: -x[1])[:5]],
        "price_range": {"min": min(prices) if prices else 0, "max": max(prices) if prices else 0, "avg": sum(prices) / len(prices) if prices else 0},
        "stock": {"in_stock": in_stock, "out_of_stock": len(items) - in_stock},
    }


_popularity_data: dict[str, float] = {}
_popularity_loaded: float = 0.0


async def _load_popularity() -> dict[str, float]:
    """Загружает popularity_score из продаж 1С."""
    global _popularity_data, _popularity_loaded
    now = time.time()
    if _popularity_loaded > now - 3600 and _popularity_data:
        return _popularity_data

    try:
        from src.clients.c1_client import C1Client

        c1 = C1Client()
        try:
            sales = await c1.get_sales(date_from=(datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"), date_to=datetime.utcnow().strftime("%Y-%m-%d"))
        finally:
            await c1.close()

        counts: dict[str, float] = {}
        for s in sales:
            name = s.get("nomenclature", "")
            if name:
                counts[name] = counts.get(name, 0) + s.get("quantity", 0)
        if counts:
            max_count = max(counts.values())
            _popularity_data = {k: v / max_count for k, v in counts.items()}
        _popularity_loaded = now
    except Exception as e:
        logger.warning("Failed to load popularity: {}", e)

    return _popularity_data


_fts_initialized = False


async def _ensure_fts() -> bool:
    global _fts_initialized
    if not _fts_initialized:
        from src.search.fts_cache import init, ensure_fresh
        init()
        _fts_initialized = True
    from src.search.fts_cache import ensure_fresh
    return await ensure_fresh(max_age=3600)


async def search_nomenclature(request: SearchRequest, items: list[dict[str, Any]] | None = None) -> SearchResponse:
    """Основной поиск номенклатуры."""
    start = time.perf_counter()

    query = request.query[:SEARCH_CONFIG.max_query_length]

    # Check mem cache
    cache_key = search_cache._make_key(query=query, filters=request.filters.model_dump() if request.filters else {}, page=request.page, limit=request.limit)
    cached = search_cache.get(cache_key)
    if cached is not None:
        return SearchResponse(**cached)

    # Try FTS5 cache first
    try:
        await _ensure_fts()
        from src.search.fts_cache import search as fts_search, search_count as fts_count

        fts_results = fts_search(query, limit=request.limit * request.page)
        if fts_results:
            items = fts_results
    except Exception as e:
        logger.warning("FTS5 search failed, fallback: {}", e)

    # Fallback: 1С batch
    if items is None:
        try:
            from src.clients.batch_client import BatchC1Client
            async with BatchC1Client() as batch:
                batch_result = await batch.execute_batch([{
                    "id": "search",
                    "method": "GET",
                    "path": "/nomenclature/search",
                    "params": {"q": query, "limit": str(min(request.limit * request.page, 500))},
                }])
                result_data = batch_result.get("results", [{}])[0].get("data") if batch_result.get("results") else None
                if result_data:
                    items = result_data
        except Exception as e:
            logger.warning("Batch search failed, fallback: {}", e)

    # Fallback: direct 1С
    if items is None:
        from src.clients.c1_client import C1Client
        c1 = C1Client()
        try:
            raw = await c1.list_nomenclature(query=query, limit=500)
        finally:
            await c1.close()
        items = raw

    scored = []
    for item in items:
        scores = calculate_score(item, query)
        if scores["total"] > 0:
            scored.append({**item, "score": scores["total"], "score_breakdown": scores})

    scored.sort(key=lambda x: -x["score"])

    filtered = apply_filters(scored, request.filters)

    total = len(filtered)
    pages = max(1, (total + request.limit - 1) // request.limit)
    page = min(request.page, pages)
    offset = (page - 1) * request.limit
    page_items = filtered[offset : offset + request.limit]

    # Enrich with stock data from 1С
    try:
        import asyncio
        from src.clients.c1_client import C1Client
        c1 = C1Client()
        try:
            stock_items = await asyncio.wait_for(c1.get_stock(), timeout=10.0)
            stock_by_name: dict[str, float] = {}
            stock_by_lower: dict[str, float] = {}
            for s in stock_items:
                name = s.get("nomenclature", "")
                qty = s.get("quantity", 0)
                if name:
                    fqty = float(qty)
                    stock_by_name[name] = stock_by_name.get(name, 0) + fqty
                    stock_by_lower[name.lower().strip()] = stock_by_lower.get(name.lower().strip(), 0) + fqty
            for item in page_items:
                name = str(item.get("name", ""))
                if name in stock_by_name:
                    item["stock_qty"] = stock_by_name[name]
                elif name.lower().strip() in stock_by_lower:
                    item["stock_qty"] = stock_by_lower[name.lower().strip()]
                else:
                    for stock_name, qty in stock_by_name.items():
                        if name.lower() in stock_name.lower() or stock_name.lower() in name.lower():
                            item["stock_qty"] = qty
                            break
        except Exception:
            pass
        finally:
            await c1.close()
    except Exception:
        pass

    results = []
    for item in page_items:
        results.append(SearchResultItem(
            id=item.get("ref", item.get("id", "")),
            name=item.get("name", ""),
            article=item.get("article", str(item.get("code", ""))),
            barcode=item.get("barcode", ""),
            group=item.get("group", item.get("item_type", "")),
            item_type=item.get("item_type", ""),
            price=item.get("price", 0.0),
            stock_qty=item.get("stock_qty", 0.0),
            score=item["score"],
            score_breakdown=item.get("score_breakdown", {}),
        ))

    facets = compute_facets(filtered)
    elapsed = (time.perf_counter() - start) * 1000

    response = SearchResponse(results=results, facets=facets, total=total, page=page, pages=pages, search_time_ms=round(elapsed, 2))

    search_cache.set(cache_key, response.model_dump())

    # Log query async
    try:
        from src.search.analytics import log_query
        log_query(user_id="api", query=query, filters=request.filters.model_dump() if request.filters else {}, results_count=total, search_time_ms=elapsed, strategy=request.strategy)
    except Exception:
        pass

    return response
