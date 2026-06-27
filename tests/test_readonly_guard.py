from __future__ import annotations

import pytest

from src.security.readonly_guard import validate_query, ReadOnlyGuardError


class TestReadOnlyGuard:
    def test_select_allowed(self):
        assert validate_query("ВЫБРАТЬ * ИЗ Номенклатура")

    def test_update_blocked(self):
        with pytest.raises(ReadOnlyGuardError):
            validate_query("ИЗМЕНИТЬ Номенклатура")

    def test_delete_blocked(self):
        with pytest.raises(ReadOnlyGuardError):
            validate_query("УДАЛИТЬ ИЗ Номенклатура")

    def test_insert_blocked(self):
        with pytest.raises(ReadOnlyGuardError):
            validate_query("ДОБАВИТЬ В Номенклатура")

    def test_drop_blocked(self):
        with pytest.raises(ReadOnlyGuardError):
            validate_query("DROP TABLE")

    def test_multiple_statements_blocked(self):
        with pytest.raises(ReadOnlyGuardError):
            validate_query("ВЫБРАТЬ *; ВЫБРАТЬ *")

    def test_complex_select_allowed(self):
        q = "ВЫБРАТЬ Т.Наименование, СУММА(Т.Количество) ИЗ Продажи КАК Т СГРУППИРОВАТЬ ПО Т.Наименование"
        assert validate_query(q)

    def test_select_with_where_allowed(self):
        q = "ВЫБРАТЬ * ИЗ Номенклатура ГДЕ Цена > 1000"
        assert validate_query(q)

    def test_comment_removed(self):
        q = "ВЫБРАТЬ * ИЗ Номенклатура // ИЗМЕНИТЬ"
        assert validate_query(q)
