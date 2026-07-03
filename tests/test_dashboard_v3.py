from __future__ import annotations

from src.dashboard.storage.models import init_db
from src.dashboard.services.dashboard_service import dashboard_repo
from src.dashboard.services.history_service import history_service
from src.dashboard.services.feedback_service import feedback_service
from src.dashboard.export.csv_exporter import export_csv
from src.dashboard.export.xlsx_exporter import export_xlsx


class TestDashboardCRUD:
    def setup_method(self):
        init_db()

    def test_create(self):
        d = dashboard_repo.create(owner_id="u1", title="Test", query="top products", chart_config={"type": "bar"})
        assert d["title"] == "Test"
        assert d["chart_config"]["type"] == "bar"

    def test_get(self):
        d = dashboard_repo.create(owner_id="u1", title="Get test", query="q", chart_config={})
        got = dashboard_repo.get(d["id"])
        assert got is not None
        assert got["title"] == "Get test"

    def test_get_not_found(self):
        assert dashboard_repo.get("nonexistent") is None

    def test_list(self):
        dashboard_repo.create(owner_id="u1", title="A", query="q", chart_config={})
        dashboard_repo.create(owner_id="u1", title="B", query="q", chart_config={})
        result = dashboard_repo.list(owner_id="u1")
        assert result["total"] >= 2

    def test_list_search(self):
        dashboard_repo.create(owner_id="u1", title="Sales Report", query="q", chart_config={})
        result = dashboard_repo.list(owner_id="u1", search="Sales")
        assert result["total"] >= 1

    def test_update(self):
        d = dashboard_repo.create(owner_id="u1", title="Old", query="q", chart_config={})
        dashboard_repo.update(d["id"], title="New")
        assert dashboard_repo.get(d["id"])["title"] == "New"

    def test_delete(self):
        d = dashboard_repo.create(owner_id="u1", title="Del", query="q", chart_config={})
        assert dashboard_repo.delete(d["id"])
        assert dashboard_repo.get(d["id"]) is None

    def test_delete_not_found(self):
        assert not dashboard_repo.delete("nope")

    def test_view_count_increments(self):
        d = dashboard_repo.create(owner_id="u1", title="Views", query="q", chart_config={})
        v1 = dashboard_repo.get(d["id"])["view_count"]
        v2 = dashboard_repo.get(d["id"])["view_count"]
        assert v2 > v1


class TestHistoryService:
    def setup_method(self):
        init_db()

    def test_log(self):
        h = history_service.log(user_id="u1", query="top products", chart_type="bar", status="success")
        assert h["status"] == "success"

    def test_list(self):
        history_service.log(user_id="u1", query="sales", chart_type="line")
        items = history_service.list(user_id="u1")
        assert len(items) >= 1

    def test_list_search(self):
        history_service.log(user_id="u1", query="sales report", chart_type="bar")
        history_service.log(user_id="u1", query="stock levels", chart_type="line")
        items = history_service.list(user_id="u1", search="sales")
        assert len(items) >= 1

    def test_link(self):
        h = history_service.log(user_id="u1", query="test", chart_type="bar")
        d = dashboard_repo.create(owner_id="u1", title="Linked", query="test", chart_config={})
        history_service.link(h["id"], d["id"])
        item = history_service.get(h["id"])
        assert item["saved_as_dashboard_id"] == d["id"]


class TestFeedback:
    def setup_method(self):
        init_db()

    def test_submit(self):
        d = dashboard_repo.create(owner_id="u1", title="FB", query="q", chart_config={})
        fb = feedback_service.submit(dashboard_id=d["id"], user_id="u1", rating="positive")
        assert fb["rating"] == "positive"

    def test_stats(self):
        d = dashboard_repo.create(owner_id="u1", title="Stats", query="q", chart_config={})
        feedback_service.submit(dashboard_id=d["id"], user_id="u1", rating="positive")
        feedback_service.submit(dashboard_id=d["id"], user_id="u2", rating="negative")
        stats = feedback_service.get_stats()
        assert stats["positive"] >= 1
        assert stats["negative"] >= 1


class TestExport:
    def test_csv(self):
        data = [{"name": "A", "value": 10}, {"name": "B", "value": 20}]
        csv_str = export_csv(data)
        assert "name" in csv_str
        assert "A" in csv_str
        assert "B" in csv_str

    def test_csv_empty(self):
        assert export_csv([]) == ""

    def test_xlsx(self):
        data = [{"name": "Test", "value": 100}]
        buf = export_xlsx(data, {"title": "Test"})
        assert buf.getvalue()[:2] == b"PK"  # XLSX is a ZIP file

    def test_xlsx_empty(self):
        buf = export_xlsx([], {})
        assert buf.getvalue()[:2] == b"PK"
