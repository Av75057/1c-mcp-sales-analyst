from __future__ import annotations

import time

from src.search.analytics import log_query, top_queries, no_results_queries, total_count


def test_log_and_read(tmp_path):
    test_data = [
        ("user1", "яблоко", {}, 5, 100.0),
        ("user1", "груша", {}, 0, 50.0),
        ("user2", "яблоко", {"in_stock": True}, 3, 200.0),
        ("user2", "ананас", {}, 0, 30.0),
    ]
    for uid, q, f, rc, t in test_data:
        log_query(uid, q, f, rc, t)

    top = top_queries(days=7, limit=10)
    assert len(top) >= 1

    no_res = no_results_queries(days=7)
    assert isinstance(no_res, list)

    total = total_count(days=7)
    assert total >= 4


def test_empty_log():
    top = top_queries(days=7)
    assert isinstance(top, list)
    no_res = no_results_queries(days=7)
    assert isinstance(no_res, list)
    total = total_count(days=7)
    assert total >= 0
