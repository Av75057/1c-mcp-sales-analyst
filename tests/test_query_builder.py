from __future__ import annotations

import pytest

from src.query.builder import build_query, validate_object_name, validate_fields_list, quote_value


class TestValidateObjectName:
    def test_valid(self):
        assert validate_object_name("Номенклатура") == "Номенклатура"

    def test_invalid_chars(self):
        with pytest.raises(ValueError):
            validate_object_name("Номенклатура; DROP")

    def test_numbers_allowed(self):
        assert validate_object_name("Товар1")


class TestValidateFields:
    def test_valid(self):
        validate_fields_list(["Наименование", "Цена"])

    def test_empty(self):
        with pytest.raises(ValueError):
            validate_fields_list([])

    def test_too_many(self):
        with pytest.raises(ValueError):
            validate_fields_list(["f"] * 51)

    def test_invalid_field(self):
        with pytest.raises(ValueError):
            validate_fields_list(["drop table"])


class TestQuoteValue:
    def test_string(self):
        assert quote_value("тест") == '"тест"'

    def test_int(self):
        assert quote_value(100) == "100"

    def test_float(self):
        assert quote_value(10.5) == "10.5"

    def test_bool_true(self):
        assert quote_value(True) == "ИСТИНА"

    def test_bool_false(self):
        assert quote_value(False) == "ЛОЖЬ"


class TestBuildQuery:
    def test_simple(self):
        q = build_query("Номенклатура", ["Наименование"])
        assert "ВЫБРАТЬ" in q
        assert "Номенклатура" in q

    def test_with_filters(self):
        q = build_query("Продажи", ["Сумма"], filters={"Цена": {">": 1000}})
        assert "ГДЕ" in q
        assert "Цена" in q

    def test_with_order(self):
        q = build_query("Товары", ["Название"], order_by=["Название УБЫВ"])
        assert "УПОРЯДОЧИТЬ ПО" in q

    def test_with_limit(self):
        q = build_query("Товары", ["Название"], limit=50)
        assert "ПРЕД 50" in q
