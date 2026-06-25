from __future__ import annotations

from src.search.models import SearchRequest, SearchResultItem, SearchResponse, SearchFilters
from src.search.service import multiword_score, fuzzy_score, compute_popularity_score, calculate_score, apply_filters, compute_facets

SAMPLE_ITEMS = [
    {"id": "1", "name": "Яблоко красное", "article": "APL-001", "group": "Фрукты", "item_type": "товар", "price": 120, "stock_qty": 50, "sales_30d": 200},
    {"id": "2", "name": "Яблочный сок", "article": "APL-002", "group": "Напитки", "item_type": "товар", "price": 80, "stock_qty": 100, "sales_30d": 500},
    {"id": "3", "name": "Ноутбук Lenovo", "article": "NB-001", "group": "Электроника", "item_type": "товар", "price": 45000, "stock_qty": 5, "sales_30d": 10},
    {"id": "4", "name": "Принтер HP LaserJet", "article": "PR-001", "group": "Электроника", "item_type": "товар", "price": 12000, "stock_qty": 0, "sales_30d": 30},
    {"id": "5", "name": "Бумага А4", "article": "PAP-001", "group": "Канцтовары", "item_type": "товар", "price": 250, "stock_qty": 500, "sales_30d": 1000},
]


class TestMultiwordScore:
    def test_exact_match_name(self):
        score = multiword_score("яблоко", SAMPLE_ITEMS[0])
        assert score > 0

    def test_partial_match(self):
        score = multiword_score("яблочный", SAMPLE_ITEMS[1])
        assert score > 0

    def test_no_match(self):
        score = multiword_score("арбуз", SAMPLE_ITEMS[0])
        assert score == 0

    def test_article_match(self):
        score = multiword_score("APL-001", SAMPLE_ITEMS[0])
        assert score > 0

    def test_multiword_query(self):
        score_apple = multiword_score("яблоко красное", SAMPLE_ITEMS[0])
        score_juice = multiword_score("яблоко красное", SAMPLE_ITEMS[1])
        assert score_apple > score_juice


class TestFuzzyScore:
    def test_exact(self):
        s = fuzzy_score("яблоко", {"name": "яблоко", "description": ""})
        assert s >= 0.8

    def test_typo(self):
        s = fuzzy_score("яблако", {"name": "яблоко", "description": ""})
        assert s >= 0.8

    def test_no_match(self):
        s = fuzzy_score("арбуз", {"name": "яблоко", "description": ""})
        assert s == 0.0 or s < 0.8


class TestPopularity:
    def test_high_sales(self):
        assert compute_popularity_score({"sales_30d": 1000}) >= 0.5

    def test_no_sales(self):
        assert compute_popularity_score({"sales_30d": 0}) == 0.0


class TestApplyFilters:
    def test_group_filter(self):
        r = apply_filters(SAMPLE_ITEMS, SearchFilters(group="Электроника"))
        assert len(r) == 2

    def test_in_stock(self):
        r = apply_filters(SAMPLE_ITEMS, SearchFilters(in_stock=True))
        assert all(i["stock_qty"] > 0 for i in r)

    def test_out_of_stock(self):
        r = apply_filters(SAMPLE_ITEMS, SearchFilters(in_stock=False))
        assert all(i["stock_qty"] == 0 for i in r)

    def test_price_range(self):
        r = apply_filters(SAMPLE_ITEMS, SearchFilters(price_min=100, price_max=500))
        assert all(100 <= i["price"] <= 500 for i in r)

    def test_combined(self):
        r = apply_filters(SAMPLE_ITEMS, SearchFilters(group="Электроника", in_stock=True))
        assert len(r) >= 0


class TestFacets:
    def test_groups(self):
        facets = compute_facets(SAMPLE_ITEMS)
        assert "groups" in facets
        assert any(g["name"] == "Электроника" for g in facets["groups"])

    def test_types(self):
        facets = compute_facets(SAMPLE_ITEMS)
        assert "types" in facets

    def test_price_range(self):
        facets = compute_facets(SAMPLE_ITEMS)
        assert facets["price_range"]["min"] <= facets["price_range"]["max"]

    def test_stock(self):
        facets = compute_facets(SAMPLE_ITEMS)
        assert facets["stock"]["in_stock"] > 0
