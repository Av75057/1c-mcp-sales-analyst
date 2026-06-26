from __future__ import annotations

from src.rag.repository import create_doc, list_docs, get_doc, update_doc, delete_doc, search_docs, get_stats, init_db


class TestKnowledgeBase:
    def setup_method(self):
        init_db()

    def test_create_doc(self):
        doc = create_doc("Test Title", "Test Content", "general", ["tag1"], "test_user")
        assert doc["title"] == "Test Title"
        assert doc["id"] is not None

    def test_get_doc(self):
        doc = create_doc("Get Test", "Content")
        fetched = get_doc(doc["id"])
        assert fetched is not None
        assert fetched["title"] == "Get Test"

    def test_get_nonexistent(self):
        assert get_doc("nonexistent") is None

    def test_list_docs(self):
        create_doc("Doc 1", "Content 1", "faq")
        create_doc("Doc 2", "Content 2", "faq")
        docs = list_docs(doc_type="faq")
        assert len(docs) >= 2

    def test_list_all(self):
        create_doc("All 1", "C1")
        create_doc("All 2", "C2")
        docs = list_docs()
        assert len(docs) >= 2

    def test_update_doc(self):
        doc = create_doc("Old", "Old content")
        update_doc(doc["id"], title="New", content="New content")
        updated = get_doc(doc["id"])
        assert updated["title"] == "New"

    def test_delete_doc(self):
        doc = create_doc("To Delete", "Content")
        delete_doc(doc["id"])
        assert get_doc(doc["id"]) is None or not get_doc(doc["id"])["is_active"]

    def test_search(self):
        create_doc("Скидка на товар", "Правило расчёта скидки для постоянных клиентов", "business_rule")
        results = search_docs("скидка")
        assert len(results) >= 1

    def test_search_no_results(self):
        results = search_docs("zzzznonexistent12345")
        assert len(results) == 0

    def test_stats(self):
        create_doc("Stats 1", "C", "faq")
        create_doc("Stats 2", "C", "business_rule")
        stats = get_stats()
        assert stats["total_documents"] >= 2
