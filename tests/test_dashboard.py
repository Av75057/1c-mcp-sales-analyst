from __future__ import annotations

import pytest

from src.dashboard.guardrails import validate_chart_config, GuardrailError
from src.dashboard.schemas import ChartConfig, Axis, Series, OnecQuery, DrillDown


class TestSchemas:
    def test_valid_chart_config(self):
        c = ChartConfig(chart_type="line", title="Test", x_axis=Axis(field="Дата", label="Дата", type="time"), y_axis=Axis(field="Сумма", label="Сумма", type="category"), series=[Series(name="S1", field="Сумма")], onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["Дата", "Сумма"]))
        assert c.chart_type == "line"

    def test_invalid_chart_type(self):
        with pytest.raises(Exception):
            ChartConfig(chart_type="invalid", title="T", x_axis=Axis(field="f", label="f", type="time"), y_axis=Axis(field="f", label="f", type="category"), series=[Series(name="S", field="f")], onec_query=OnecQuery(entity="E", fields=["f"]))

    def test_default_period(self):
        c = ChartConfig(chart_type="bar", title="T", x_axis=Axis(field="f", label="f", type="category"), y_axis=Axis(field="f", label="f", type="category"), series=[Series(name="S", field="f")], onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["f"]))
        assert c.onec_query.period == "last_30_days"


class TestGuardrails:
    def test_valid_entity(self):
        validate_chart_config({"onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Дата", "Сумма"]}, "chart_type": "line", "drill_down": {"enabled": False}})

    def test_invalid_entity(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({"onec_query": {"entity": "Invalid.Entity", "fields": []}, "chart_type": "bar", "drill_down": {"enabled": False}})

    def test_invalid_field(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({"onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["InvalidField"]}, "chart_type": "line", "drill_down": {"enabled": False}})

    def test_pie_limit_capped(self):
        c = {"onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма"]}, "chart_type": "pie", "limit": 10, "drill_down": {"enabled": False}}
        validate_chart_config(c)
        assert c["limit"] == 7
