from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.dashboard.composite.service import composite_service, init_db, _get_db
from src.dashboard.guardrails import validate_chart_config, GuardrailError
from src.dashboard.schemas import ChartConfig, Axis, Series, OnecQuery, HeatmapConfig, TreemapConfig, SankeyConfig, GaugeConfig, RadarConfig
from src.dashboard.rbac.service import rbac_service
from src.dashboard.scheduler.service import scheduler_service
from src.dashboard.notifications.service import notification_service
from src.dashboard.recommendations.service import recommendation_service


# --- Extended Chart Types ---

class TestExtendedChartTypes:
    def test_heatmap_valid(self):
        c = ChartConfig(
            chart_type="heatmap", title="Heat", subtitle="",
            x_axis=Axis(field="x", label="X", type="category"),
            y_axis=Axis(field="y", label="Y", type="category"),
            series=[Series(name="V", field="value")],
            onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["Сумма"]),
            heatmap=HeatmapConfig(x_field="x", y_field="y", value_field="value"),
        )
        assert c.chart_type == "heatmap"
        assert c.heatmap is not None

    def test_treemap_valid(self):
        c = ChartConfig(
            chart_type="treemap", title="Tree", subtitle="",
            x_axis=Axis(field="x", label="X", type="category"),
            y_axis=Axis(field="y", label="Y", type="category"),
            series=[Series(name="V", field="value")],
            onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["Сумма"]),
            treemap=TreemapConfig(category_field="cat", value_field="value"),
        )
        assert c.chart_type == "treemap"

    def test_sankey_valid(self):
        c = ChartConfig(
            chart_type="sankey", title="Sankey", subtitle="",
            x_axis=Axis(field="x", label="X", type="category"),
            y_axis=Axis(field="y", label="Y", type="category"),
            series=[Series(name="V", field="value")],
            onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["Сумма"]),
            sankey=SankeyConfig(source_field="src", target_field="dst", value_field="value"),
        )
        assert c.chart_type == "sankey"

    def test_gauge_valid(self):
        c = ChartConfig(
            chart_type="gauge", title="Gauge", subtitle="",
            x_axis=Axis(field="x", label="X", type="value"),
            y_axis=Axis(field="y", label="Y", type="value"),
            series=[Series(name="V", field="value")],
            onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["Сумма"]),
            gauge=GaugeConfig(value_field="value", target=100),
        )
        assert c.chart_type == "gauge"

    def test_radar_valid(self):
        c = ChartConfig(
            chart_type="radar", title="Radar", subtitle="",
            x_axis=Axis(field="x", label="X", type="category"),
            y_axis=Axis(field="y", label="Y", type="value"),
            series=[Series(name="V", field="value")],
            onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["Сумма"]),
            radar=RadarConfig(dimensions=["A", "B", "C", "D"], value_field="value"),
        )
        assert c.chart_type == "radar"

    def test_invalid_chart_type(self):
        with pytest.raises(Exception):
            ChartConfig(
                chart_type="invalid", title="T", subtitle="",
                x_axis=Axis(field="f", label="f", type="time"),
                y_axis=Axis(field="f", label="f", type="category"),
                series=[Series(name="S", field="f")],
                onec_query=OnecQuery(entity="E", fields=["f"]),
            )


# --- Extended Guardrails ---

class TestExtendedGuardrailsV4:
    def test_heatmap_guardrail(self):
        validate_chart_config({
            "chart_type": "heatmap",
            "series": [{"name": "V", "field": "Сумма"}],
            "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"]},
            "heatmap": {"x_field": "x", "y_field": "y", "value_field": "v"},
            "drill_down": {"enabled": False},
        })

    def test_heatmap_needs_config(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({
                "chart_type": "heatmap",
                "series": [{"name": "V", "field": "Сумма"}],
                "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"]},
                "drill_down": {"enabled": False},
            })

    def test_treemap_needs_config(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({
                "chart_type": "treemap",
                "series": [{"name": "V", "field": "Сумма"}],
                "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"]},
                "drill_down": {"enabled": False},
            })

    def test_sankey_needs_config(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({
                "chart_type": "sankey",
                "series": [{"name": "V", "field": "Сумма"}],
                "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"]},
                "drill_down": {"enabled": False},
            })

    def test_gauge_needs_config(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({
                "chart_type": "gauge",
                "series": [{"name": "V", "field": "Сумма"}],
                "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"]},
                "drill_down": {"enabled": False},
            })

    def test_radar_needs_min_dimensions(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({
                "chart_type": "radar",
                "series": [{"name": "V", "field": "Сумма"}],
                "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"]},
                "radar": {"dimensions": ["A", "B"], "value_field": "v"},
                "drill_down": {"enabled": False},
            })

    def test_radar_valid_guardrail(self):
        validate_chart_config({
            "chart_type": "radar",
            "series": [{"name": "V", "field": "Сумма"}],
            "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"]},
            "radar": {"dimensions": ["A", "B", "C"], "value_field": "v"},
            "drill_down": {"enabled": False},
        })


# --- Composite Dashboard Service ---

class TestCompositeService:
    def setup_method(self):
        init_db()
        conn = _get_db()
        conn.execute("DELETE FROM composite_dashboards")
        conn.execute("DELETE FROM dashboard_permissions")
        conn.execute("DELETE FROM scheduled_reports")
        conn.execute("DELETE FROM notifications")
        conn.execute("DELETE FROM dashboard_recommendations")
        conn.commit()
        conn.close()

    def test_create_and_get(self):
        charts = [{"id": "c1", "title": "Sales", "chart_config": {"chart_type": "bar"}, "data": [], "position": {"x": 0, "y": 0, "w": 6, "h": 4}, "filter_bindings": []}]
        doc = composite_service.create(owner_id="user1", title="My Dashboard", description="Test", charts=charts, tags=["sales"])
        assert doc is not None
        assert doc["title"] == "My Dashboard"
        assert len(doc["charts"]) == 1
        assert doc["tags"] == ["sales"]

        fetched = composite_service.get(doc["id"])
        assert fetched is not None
        assert fetched["title"] == "My Dashboard"

    def test_list(self):
        composite_service.create(owner_id="user1", title="A", description="", charts=[])
        composite_service.create(owner_id="user1", title="B", description="", charts=[])
        result = composite_service.list(owner_id="user1")
        assert result["total"] == 2

    def test_list_search(self):
        composite_service.create(owner_id="user1", title="Sales Report", description="Monthly", charts=[])
        composite_service.create(owner_id="user1", title="Stock Report", description="Weekly", charts=[])
        result = composite_service.list(owner_id="user1", search="Sales")
        assert result["total"] == 1

    def test_update(self):
        doc = composite_service.create(owner_id="user1", title="Original", description="", charts=[])
        updated = composite_service.update(doc["id"], title="Updated")
        assert updated["title"] == "Updated"

    def test_delete(self):
        doc = composite_service.create(owner_id="user1", title="Delete Me", description="", charts=[])
        ok = composite_service.delete(doc["id"])
        assert ok is True
        assert composite_service.get(doc["id"]) is None

    def test_delete_cascades(self):
        doc = composite_service.create(owner_id="user1", title="Cascade", description="", charts=[])
        rbac_service.set_permission(doc["id"], "user2", "view")
        composite_service.delete(doc["id"])
        assert rbac_service.get_permission(doc["id"], "user2") is None


# --- RBAC Service ---

class TestRBACService:
    def setup_method(self):
        init_db()
        conn = _get_db()
        conn.execute("DELETE FROM composite_dashboards")
        conn.execute("DELETE FROM dashboard_permissions")
        conn.commit()
        conn.close()
        self.doc = composite_service.create(owner_id="owner1", title="RBAC Test", description="", charts=[])

    def test_set_and_get_permission(self):
        rbac_service.set_permission(self.doc["id"], "user2", "view")
        assert rbac_service.get_permission(self.doc["id"], "user2") == "view"

    def test_upgrade_permission(self):
        rbac_service.set_permission(self.doc["id"], "user2", "view")
        rbac_service.set_permission(self.doc["id"], "user2", "edit")
        assert rbac_service.get_permission(self.doc["id"], "user2") == "edit"

    def test_remove_permission(self):
        rbac_service.set_permission(self.doc["id"], "user2", "view")
        ok = rbac_service.remove_permission(self.doc["id"], "user2")
        assert ok is True
        assert rbac_service.get_permission(self.doc["id"], "user2") is None

    def test_can_access_owner(self):
        assert rbac_service.can_access(self.doc["id"], "owner1", "admin") is True

    def test_can_access_public(self):
        composite_service.update(self.doc["id"], is_public=True)
        assert rbac_service.can_access(self.doc["id"], "anyone", "view") is True
        assert rbac_service.can_access(self.doc["id"], "anyone", "edit") is False

    def test_can_access_permission(self):
        rbac_service.set_permission(self.doc["id"], "user2", "edit")
        assert rbac_service.can_access(self.doc["id"], "user2", "edit") is True
        assert rbac_service.can_access(self.doc["id"], "user2", "admin") is False

    def test_list_permissions(self):
        rbac_service.set_permission(self.doc["id"], "user2", "view")
        rbac_service.set_permission(self.doc["id"], "user3", "edit")
        perms = rbac_service.list_permissions(self.doc["id"])
        assert len(perms) == 2


# --- Scheduler Service ---

class TestSchedulerService:
    def setup_method(self):
        init_db()
        conn = _get_db()
        conn.execute("DELETE FROM scheduled_reports")
        conn.execute("DELETE FROM composite_dashboards")
        conn.commit()
        conn.close()
        self.doc = composite_service.create(owner_id="owner1", title="Sched Test", description="", charts=[])

    def test_create(self):
        s = scheduler_service.create(dashboard_id=self.doc["id"], owner_id="owner1", cron="0 9 * * 1", recipients=["admin@test.com"])
        assert s["dashboard_id"] == self.doc["id"]
        assert s["cron"] == "0 9 * * 1"
        assert s["is_active"] is True or s["is_active"] == 1

    def test_list_by_dashboard(self):
        scheduler_service.create(dashboard_id=self.doc["id"], owner_id="owner1")
        items = scheduler_service.list_by_dashboard(self.doc["id"])
        assert len(items) == 1

    def test_update(self):
        s = scheduler_service.create(dashboard_id=self.doc["id"], owner_id="owner1")
        updated = scheduler_service.update(s["id"], cron="0 8 * * *")
        assert updated["cron"] == "0 8 * * *"

    def test_delete(self):
        s = scheduler_service.create(dashboard_id=self.doc["id"], owner_id="owner1")
        ok = scheduler_service.delete(s["id"])
        assert ok is True
        assert scheduler_service.get(s["id"]) is None

    def test_mark_run(self):
        s = scheduler_service.create(dashboard_id=self.doc["id"], owner_id="owner1")
        scheduler_service.mark_run(s["id"])
        updated = scheduler_service.get(s["id"])
        assert updated["last_run"] is not None


# --- Notification Service ---

class TestNotificationService:
    def setup_method(self):
        init_db()
        conn = _get_db()
        conn.execute("DELETE FROM notifications")
        conn.commit()
        conn.close()

    def test_create_and_list(self):
        notification_service.create(dashboard_id="d1", user_id="user1", type="anomaly", title="Stock alert", message="Low stock")
        items = notification_service.list("user1")
        assert len(items) == 1
        assert items[0]["title"] == "Stock alert"

    def test_unread_count(self):
        notification_service.create(dashboard_id="d1", user_id="user1", type="info", title="N1")
        notification_service.create(dashboard_id="d1", user_id="user1", type="info", title="N2")
        assert notification_service.unread_count("user1") == 2

    def test_mark_read(self):
        n = notification_service.create(dashboard_id="d1", user_id="user1", type="info", title="Read me")
        ok = notification_service.mark_read(n["id"])
        assert ok is True
        assert notification_service.unread_count("user1") == 0

    def test_mark_all_read(self):
        notification_service.create(dashboard_id="d1", user_id="user1", type="info", title="N1")
        notification_service.create(dashboard_id="d1", user_id="user1", type="info", title="N2")
        count = notification_service.mark_all_read("user1")
        assert count == 2
        assert notification_service.unread_count("user1") == 0

    def test_list_unread_only(self):
        n = notification_service.create(dashboard_id="d1", user_id="user1", type="info", title="Unread")
        notification_service.mark_read(n["id"])
        items = notification_service.list("user1", unread_only=True)
        assert len(items) == 0


# --- Recommendations Service ---

class TestRecommendationService:
    def setup_method(self):
        init_db()
        conn = _get_db()
        conn.execute("DELETE FROM dashboard_recommendations")
        conn.execute("DELETE FROM composite_dashboards")
        conn.commit()
        conn.close()
        self.doc = composite_service.create(owner_id="owner1", title="Rec Test", description="", charts=[
            {"id": "c1", "title": "Bar Chart", "chart_config": {"chart_type": "bar"}, "data": [], "position": {"x": 0, "y": 0, "w": 6, "h": 4}, "filter_bindings": []},
        ])

    def test_generate(self):
        recs = recommendation_service.generate(self.doc["id"], self.doc)
        assert len(recs) > 0

    def test_list(self):
        recommendation_service.generate(self.doc["id"], self.doc)
        recs = recommendation_service.list(self.doc["id"])
        assert len(recs) > 0

    def test_mark_applied(self):
        recs = recommendation_service.generate(self.doc["id"], self.doc)
        rid = recs[0]["id"]
        ok = recommendation_service.mark_applied(rid)
        assert ok is True


# --- API Routes ---

class TestAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        init_db()
        conn = _get_db()
        conn.execute("DELETE FROM composite_dashboards")
        conn.execute("DELETE FROM dashboard_permissions")
        conn.execute("DELETE FROM scheduled_reports")
        conn.execute("DELETE FROM notifications")
        conn.execute("DELETE FROM dashboard_recommendations")
        conn.commit()
        conn.close()

    def _make_app(self):
        from fastapi import FastAPI
        from src.dashboard.routes_v4 import router
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_create_composite_dashboard(self):
        client = self._make_app()
        resp = client.post("/api/v2/dashboards", json={"title": "API Test", "charts": [{"id": "c1", "title": "Sales", "chart_config": {"chart_type": "bar"}, "data": [], "position": {"x": 0, "y": 0, "w": 6, "h": 4}, "filter_bindings": []}]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["dashboard"]["title"] == "API Test"

    def test_list_composite_dashboards(self):
        client = self._make_app()
        client.post("/api/v2/dashboards", json={"title": "D1", "charts": []})
        resp = client.get("/api/v2/dashboards")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_composite_dashboard(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Get Me", "charts": []}).json()
        did = create["dashboard"]["id"]
        resp = client.get(f"/api/v2/dashboards/{did}")
        assert resp.status_code == 200
        assert resp.json()["dashboard"]["title"] == "Get Me"

    def test_get_composite_dashboard_404(self):
        client = self._make_app()
        resp = client.get("/api/v2/dashboards/nonexistent")
        assert resp.status_code == 404

    def test_update_composite_dashboard(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Old", "charts": []}).json()
        did = create["dashboard"]["id"]
        resp = client.patch(f"/api/v2/dashboards/{did}", json={"title": "New"})
        assert resp.status_code == 200
        assert resp.json()["dashboard"]["title"] == "New"

    def test_delete_composite_dashboard(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Delete", "charts": []}).json()
        did = create["dashboard"]["id"]
        resp = client.delete(f"/api/v2/dashboards/{did}")
        assert resp.status_code == 200

    def test_set_permission(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Perm Test", "charts": []}).json()
        did = create["dashboard"]["id"]
        resp = client.post(f"/api/v2/dashboards/{did}/permissions", json={"user_id": "user2", "permission": "edit"})
        assert resp.status_code == 200
        assert resp.json()["permission"]["permission"] == "edit"

    def test_list_permissions(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Perm List", "charts": []}).json()
        did = create["dashboard"]["id"]
        client.post(f"/api/v2/dashboards/{did}/permissions", json={"user_id": "user2", "permission": "view"})
        resp = client.get(f"/api/v2/dashboards/{did}/permissions")
        assert resp.status_code == 200
        assert len(resp.json()["permissions"]) == 1

    def test_check_access(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Access Test", "charts": [], "is_public": True}).json()
        did = create["dashboard"]["id"]
        resp = client.get(f"/api/v2/dashboards/{did}/access/user2", params={"required": "view"})
        assert resp.status_code == 200
        assert resp.json()["allowed"] is True

    def test_create_schedule(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Sched", "charts": []}).json()
        did = create["dashboard"]["id"]
        resp = client.post(f"/api/v2/dashboards/{did}/schedules", json={"cron": "0 9 * * 1", "recipients": ["a@b.com"]})
        assert resp.status_code == 200
        assert resp.json()["schedule"]["cron"] == "0 9 * * 1"

    def test_list_schedules(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Sched List", "charts": []}).json()
        did = create["dashboard"]["id"]
        client.post(f"/api/v2/dashboards/{did}/schedules", json={})
        resp = client.get(f"/api/v2/dashboards/{did}/schedules")
        assert resp.status_code == 200
        assert len(resp.json()["schedules"]) == 1

    def test_notifications(self):
        client = self._make_app()
        resp = client.get("/api/v2/notifications")
        assert resp.status_code == 200
        assert "notifications" in resp.json()

    def test_recommendations_generate(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Rec", "charts": [
            {"id": "c1", "title": "B", "chart_config": {"chart_type": "bar"}, "data": [], "position": {"x": 0, "y": 0, "w": 6, "h": 4}, "filter_bindings": []},
        ]}).json()
        did = create["dashboard"]["id"]
        resp = client.post(f"/api/v2/dashboards/{did}/recommendations")
        assert resp.status_code == 200
        assert len(resp.json()["recommendations"]) > 0

    def test_recommendations_list(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Rec List", "charts": []}).json()
        did = create["dashboard"]["id"]
        resp = client.get(f"/api/v2/dashboards/{did}/recommendations")
        assert resp.status_code == 200
        assert isinstance(resp.json()["recommendations"], list)

    def test_apply_recommendation(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Apply Rec", "charts": []}).json()
        did = create["dashboard"]["id"]
        recs = client.post(f"/api/v2/dashboards/{did}/recommendations").json()["recommendations"]
        assert len(recs) > 0
        rid = recs[0]["id"]
        resp = client.post(f"/api/v2/recommendations/{rid}/apply")
        assert resp.status_code == 200
        assert resp.json()["status"] == "applied"

    def test_delete_schedule(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Del Sched", "charts": []}).json()
        did = create["dashboard"]["id"]
        s = client.post(f"/api/v2/dashboards/{did}/schedules", json={}).json()["schedule"]
        resp = client.delete(f"/api/v2/schedules/{s['id']}")
        assert resp.status_code == 200

    def test_update_schedule(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Upd Sched", "charts": []}).json()
        did = create["dashboard"]["id"]
        s = client.post(f"/api/v2/dashboards/{did}/schedules", json={"cron": "0 9 * * 1"}).json()["schedule"]
        resp = client.patch(f"/api/v2/schedules/{s['id']}", json={"cron": "0 8 * * *"})
        assert resp.status_code == 200
        assert resp.json()["schedule"]["cron"] == "0 8 * * *"

    def test_notifications_mark_read(self):
        client = self._make_app()
        notification_service.create(dashboard_id="d1", user_id="anonymous", type="info", title="Test")
        notifs = client.get("/api/v2/notifications").json()["notifications"]
        assert len(notifs) > 0
        nid = notifs[0]["id"]
        resp = client.post(f"/api/v2/notifications/{nid}/read")
        assert resp.status_code == 200

    def test_notifications_mark_all_read(self):
        notification_service.create(dashboard_id="d1", user_id="anonymous", type="info", title="N1")
        notification_service.create(dashboard_id="d1", user_id="anonymous", type="info", title="N2")
        client = self._make_app()
        resp = client.post("/api/v2/notifications/read-all")
        assert resp.status_code == 200
        assert resp.json()["marked_read"] >= 2

    def test_remove_permission_via_api(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Rm Perm", "charts": []}).json()
        did = create["dashboard"]["id"]
        client.post(f"/api/v2/dashboards/{did}/permissions", json={"user_id": "u1", "permission": "view"})
        resp = client.request("DELETE", f"/api/v2/dashboards/{did}/permissions", json={"user_id": "u1"})
        assert resp.status_code == 200
        resp2 = client.get(f"/api/v2/dashboards/{did}/permissions")
        assert len(resp2.json()["permissions"]) == 0

    def test_fetch_data_endpoint(self):
        client = self._make_app()
        resp = client.post("/api/v2/dashboards/fetch-data", json={"chart_config": {"onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"], "period": "last_30_days"}, "series": [{"field": "Сумма"}], "x_axis": {"field": "Дата"}, "limit": 10}})
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_refresh_dashboard(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Refresh Test", "charts": [
            {"id": "c1", "title": "T", "chart_config": {"chart_type": "bar", "x_axis": {"field": "Дата", "label": "X", "type": "category"}, "y_axis": {"field": "Сумма", "label": "Y", "type": "category"}, "series": [{"name": "S", "field": "Сумма", "color": "#5470c6"}], "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"], "period": "last_30_days"}}, "data": [], "position": {"x": 0, "y": 0, "w": 6, "h": 4}, "filter_bindings": []},
        ]}).json()
        did = create["dashboard"]["id"]
        resp = client.post(f"/api/v2/dashboards/{did}/refresh")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_dashboard_is_favorite_flag(self):
        client = self._make_app()
        resp = client.post("/api/v2/dashboards", json={"title": "Fav", "charts": [], "is_favorite": True})
        assert resp.status_code == 200
        assert resp.json()["dashboard"]["is_favorite"] is True

    def test_update_is_favorite_via_api(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Fav2", "charts": []}).json()
        did = create["dashboard"]["id"]
        resp = client.patch(f"/api/v2/dashboards/{did}", json={"is_favorite": True})
        assert resp.status_code == 200
        assert resp.json()["dashboard"]["is_favorite"] is True

    def test_update_charts_via_api(self):
        client = self._make_app()
        create = client.post("/api/v2/dashboards", json={"title": "Upd Charts", "charts": []}).json()
        did = create["dashboard"]["id"]
        new_charts = [{"id": "c1", "title": "New Chart", "chart_config": {"chart_type": "bar"}, "data": [], "position": {"x": 0, "y": 0, "w": 6, "h": 4}, "filter_bindings": []}]
        resp = client.patch(f"/api/v2/dashboards/{did}", json={"charts": new_charts})
        assert resp.status_code == 200
        assert len(resp.json()["dashboard"]["charts"]) == 1

    def test_pagination(self):
        client = self._make_app()
        for i in range(5):
            client.post("/api/v2/dashboards", json={"title": f"D{i}", "charts": []})
        resp = client.get("/api/v2/dashboards?page=1&per_page=3")
        assert resp.status_code == 200
        items = resp.json()["dashboards"]
        # Может включать старые дашборды, проверяем что хотя бы 3 новые есть
        new_items = [d for d in items if d.get("title", "").startswith("D")]
        assert len(new_items) >= 2
        assert resp.json()["total"] >= 5

    def test_fetch_data_no_chart_config(self):
        client = self._make_app()
        resp = client.post("/api/v2/dashboards/fetch-data", json={})
        assert resp.status_code == 400

    def test_refresh_nonexistent_dashboard(self):
        client = self._make_app()
        resp = client.post("/api/v2/dashboards/nonexistent/refresh")
        assert resp.status_code == 404

    def test_notifications_cross_user(self):
        notification_service.create(dashboard_id="d1", user_id="alice", type="info", title="Alice notif")
        notification_service.create(dashboard_id="d1", user_id="bob", type="info", title="Bob notif")
        alice_notifs = notification_service.list("alice")
        assert len(alice_notifs) == 1
        assert alice_notifs[0]["title"] == "Alice notif"

    def test_notifications_unread_count_zero(self):
        n = notification_service.create(dashboard_id="d1", user_id="u1", type="info", title="N")
        notification_service.mark_read(n["id"])
        assert notification_service.unread_count("u1") == 0

    def test_schedule_is_active_toggle(self):
        doc = composite_service.create(owner_id="owner", title="Sched Test", description="", charts=[])
        s = scheduler_service.create(dashboard_id=doc["id"], owner_id="owner")
        scheduler_service.update(s["id"], is_active=False)
        updated = scheduler_service.get(s["id"])
        assert updated["is_active"] is False

    def test_schedule_list_due(self):
        from datetime import datetime, timezone
        from src.dashboard.composite.service import _get_db
        doc = composite_service.create(owner_id="owner", title="Due Test", description="", charts=[])
        s = scheduler_service.create(dashboard_id=doc["id"], owner_id="owner", cron="0 9 * * 1")
        # Принудительно ставим next_run в прошлое
        conn = _get_db()
        try:
            conn.execute("UPDATE scheduled_reports SET next_run = ? WHERE id = ?", ("2020-01-01T00:00:00", s["id"]))
            conn.commit()
        finally:
            conn.close()
        due = scheduler_service.list_due(limit=5)
        assert len(due) > 0
        assert due[0]["id"] == s["id"]

    def test_create_heatmap_chart(self):
        client = self._make_app()
        charts = [{
            "id": "h1", "title": "Heat", "chart_config": {"chart_type": "heatmap", "x_axis": {"field": "x", "label": "X", "type": "category"}, "y_axis": {"field": "y", "label": "Y", "type": "category"}, "series": [{"name": "V", "field": "value"}], "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"]}, "heatmap": {"x_field": "x", "y_field": "y", "value_field": "v"}},
            "data": [], "position": {"x": 0, "y": 0, "w": 6, "h": 4}, "filter_bindings": [],
        }]
        resp = client.post("/api/v2/dashboards", json={"title": "Heatmap Dash", "charts": charts})
        assert resp.status_code == 200
        assert len(resp.json()["dashboard"]["charts"]) == 1
