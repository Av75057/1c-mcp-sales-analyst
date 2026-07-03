from __future__ import annotations

import pytest

from src.dashboard.schemas import ChartConfig, Axis, Series, OnecQuery
from src.dashboard.guardrails import validate_chart_config, GuardrailError
from src.dashboard.period_comparator import resolve_period, compute_comparison
from src.dashboard.error_handler import handle_error


class TestExtendedSchemas:
    def test_horizontal_bar_valid(self):
        c = ChartConfig(chart_type="horizontal_bar", title="Test", x_axis=Axis(field="f", label="f", type="category"), y_axis=Axis(field="f", label="f", type="category"), series=[Series(name="S", field="f")], onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["f"]))
        assert c.chart_type == "horizontal_bar"

    def test_combo_valid(self):
        c = ChartConfig(chart_type="combo", title="Test", x_axis=Axis(field="f", label="f", type="category"), y_axis=Axis(field="f", label="f", type="category"), series=[Series(name="S1", field="f1"), Series(name="S2", field="f2")], onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["f1", "f2"]))
        assert c.chart_type == "combo"

    def test_scatter_valid(self):
        ChartConfig(chart_type="scatter", title="T", x_axis=Axis(field="f", label="f", type="value"), y_axis=Axis(field="f", label="f", type="value"), series=[Series(name="S", field="f")], onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["f"]))

    def test_area_valid(self):
        ChartConfig(chart_type="area", title="T", x_axis=Axis(field="f", label="f", type="time"), y_axis=Axis(field="f", label="f", type="category"), series=[Series(name="S", field="f")], onec_query=OnecQuery(entity="Document.РеализацияТоваровУслуг", fields=["f"]))

    def test_invalid_chart_type(self):
        with pytest.raises(Exception):
            ChartConfig(chart_type="invalid", title="T", x_axis=Axis(field="f", label="f", type="time"), y_axis=Axis(field="f", label="f", type="category"), series=[Series(name="S", field="f")], onec_query=OnecQuery(entity="E", fields=["f"]))


class TestExtendedGuardrails:
    def test_valid_combo(self):
        validate_chart_config({"chart_type": "combo", "series": [{"name": "A", "field": "Сумма", "type": "bar"}, {"name": "B", "field": "Количество", "type": "line"}], "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["Сумма", "Количество"]}, "drill_down": {"enabled": False}})

    def test_combo_needs_two_series(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({"chart_type": "combo", "series": [{"name": "A", "field": "a"}], "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["a"]}, "drill_down": {"enabled": False}})

    def test_scatter_needs_value_axis(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({"chart_type": "scatter", "series": [{"name": "A", "field": "a"}], "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["a"]}, "x_axis": {"type": "category"}, "drill_down": {"enabled": False}})

    def test_filter_operator_validation(self):
        with pytest.raises(GuardrailError):
            validate_chart_config({"chart_type": "bar", "series": [{"name": "A", "field": "a"}], "onec_query": {"entity": "Document.РеализацияТоваровУслуг", "fields": ["a"]}, "filters": [{"field": "Сумма", "operator": "invalid", "value": 100}], "drill_down": {"enabled": False}})


class TestPeriodComparator:
    def test_resolve_period(self):
        f, t = resolve_period("last_30_days")
        assert f < t

    def test_compute_comparison_enabled(self):
        config = {"comparison": {"enabled": True, "type": "previous_period"}, "chart_type": "line", "series": [{"name": "Cur", "field": "sum"}], "onec_query": {"entity": "E", "fields": ["sum"], "period": "last_30_days", "aggregation": "sum"}}
        result = compute_comparison(config)
        assert result["comparison"]["current_period"] is not None
        assert result["comparison"]["comparison_period"] is not None
        assert result["chart_type"] == "combo"

    def test_compute_comparison_disabled(self):
        config = {"comparison": {"enabled": False}, "chart_type": "line", "series": [{"name": "S", "field": "f"}], "onec_query": {"entity": "E", "fields": ["f"], "period": "last_30_days", "aggregation": "sum"}}
        result = compute_comparison(config)
        assert result["chart_type"] == "line"

    def test_resolve_week(self):
        f, t = resolve_period("last_7_days")
        assert (t - f).days <= 8


class TestErrorHandler:
    def test_guardrail_error(self):
        err = GuardrailError("Invalid field")
        result = handle_error(err)
        assert result["error_code"] == "INVALID_QUERY"

    def test_no_data_error(self):
        err = ValueError("No data found")
        result = handle_error(err)
        assert result["error_code"] == "NO_DATA"

    def test_unknown_error(self):
        err = RuntimeError("something bad")
        result = handle_error(err)
        assert result["error_code"] == "INTERNAL_ERROR"
