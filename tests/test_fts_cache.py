from __future__ import annotations

import os
import tempfile

from src.search import fts_cache

SAMPLE = [
    {"ref": "1", "name": "Яблоко красное", "article": "APL-001", "group": "Фрукты", "item_type": "товар", "price": 120, "stock_qty": 50},
    {"ref": "2", "name": "Ноутбук Lenovo", "article": "NB-001", "group": "Электроника", "item_type": "товар", "price": 45000, "stock_qty": 5},
    {"ref": "3", "name": "Принтер HP LaserJet", "article": "PR-001", "group": "Электроника", "item_type": "товар", "price": 12000, "stock_qty": 0},
    {"ref": "4", "name": "Бумага А4 офсетная", "article": "PAP-001", "group": "Канцтовары", "item_type": "товар", "price": 250, "stock_qty": 500},
    {"ref": "5", "name": "Яблочный сок", "article": "APL-002", "group": "Напитки", "item_type": "товар", "price": 80, "stock_qty": 100},
]


def setup_module():
    # Use temp db for tests
    fts_cache.DB_PATH = fts_cache.DB_PATH.parent / "test_nomenclature_cache.db"
    fts_cache.init()


def teardown_module():
    if fts_cache.DB_PATH.exists():
        fts_cache.DB_PATH.unlink()


class TestFtsCache:
    def test_init_creates_tables(self):
        fts_cache.init()
        assert fts_cache.DB_PATH.exists()

    def test_initial_needs_refresh(self):
        assert fts_cache.needs_refresh(max_age=0)

    def test_refresh(self):
        count = fts_cache.refresh(SAMPLE)
        assert count == 5

    def test_after_refresh_no_needs(self):
        assert not fts_cache.needs_refresh(max_age=3600)

    def test_search_exact(self):
        results = fts_cache.search("яблоко")
        assert len(results) >= 1
        names = [r["name"] for r in results]
        assert any("яблоко" in n.lower() for n in names)

    def test_search_multiword(self):
        results = fts_cache.search("яблочный сок")
        assert len(results) >= 1
        assert results[0]["name"] == "Яблочный сок"

    def test_search_article(self):
        results = fts_cache.search("APL-001")
        assert len(results) >= 1
        assert results[0]["article"] == "APL-001"

    def test_search_no_results(self):
        results = fts_cache.search("zzzznonexistent")
        assert len(results) == 0

    def test_search_limit(self):
        results = fts_cache.search("а", limit=2)
        assert len(results) <= 2

    def test_search_count(self):
        count = fts_cache.search_count("яблоко")
        assert count >= 1

    def test_search_score(self):
        results = fts_cache.search("яблоко")
        for r in results:
            assert 0.0 <= r["score"] <= 1.0

    def test_refresh_clears_old(self):
        fts_cache.refresh(SAMPLE[:1])
        assert fts_cache.search_count("яблоко") == 1
        fts_cache.refresh(SAMPLE)
        assert fts_cache.search_count("яблоко") >= 1
