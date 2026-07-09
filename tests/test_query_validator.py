from __future__ import annotations

import pytest
from src.mcp.tools.query_validator import QueryValidationGuardrails, QueryValidator


class TestGuardrails:
    def test_valid_select(self):
        r = QueryValidationGuardrails.validate("ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура")
        assert r.is_valid is True

    def test_empty_query(self):
        r = QueryValidationGuardrails.validate("")
        assert r.is_valid is False
        assert "пустой" in r.error.lower()

    def test_too_long(self):
        q = "ВЫБРАТЬ " + "Поле, " * 1000
        r = QueryValidationGuardrails.validate(q)
        assert r.is_valid is False
        assert "слишком длинный" in r.error.lower()

    def test_forbidden_update(self):
        r = QueryValidationGuardrails.validate("ИЗМЕНИТЬ Справочник.Номенклатура")
        assert r.is_valid is False
        assert r.error is not None

    def test_forbidden_delete(self):
        r = QueryValidationGuardrails.validate("УДАЛИТЬ ИЗ Справочник.Номенклатура")
        assert r.is_valid is False

    def test_forbidden_insert(self):
        r = QueryValidationGuardrails.validate("INSERT INTO test VALUES (1)")
        assert r.is_valid is False

    def test_sql_injection(self):
        q = "ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура; DROP TABLE Товары"
        r = QueryValidationGuardrails.validate(q)
        assert r.is_valid is False

    def test_comment_double_dash(self):
        r = QueryValidationGuardrails.validate("ВЫБРАТЬ 1 -- DROP TABLE")
        assert r.is_valid is False

    def test_missing_select(self):
        r = QueryValidationGuardrails.validate("Наименование ИЗ Справочник.Номенклатура")
        assert r.is_valid is False
        assert "выбрать" in r.error.lower()

    def test_valid_with_params(self):
        r = QueryValidationGuardrails.validate("ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура ГДЕ Дата > &ДатаНач", {"ДатаНач": "2026-01-01"})
        assert r.is_valid is True

    def test_too_many_params(self):
        params = {f"p{i}": i for i in range(100)}
        r = QueryValidationGuardrails.validate("ВЫБРАТЬ 1", params)
        assert r.is_valid is False
        assert "много параметров" in r.error.lower()

    def test_long_param_value(self):
        r = QueryValidationGuardrails.validate("ВЫБРАТЬ 1", {"x": "a" * 600})
        assert r.is_valid is False

    def test_complex_valid(self):
        q = (
            "ВЫБРАТЬ Товары.Номенклатура.Наименование КАК Товар, "
            "СУММА(Товары.Сумма) КАК Выручка "
            "ИЗ Документ.РеализацияТоваровУслуг.Товары КАК Товары "
            "ГДЕ Товары.Ссылка.Дата МЕЖДУ &ДатаНач И &ДатаКон "
            "СГРУППИРОВАТЬ ПО Товары.Номенклатура.Наименование "
            "УПОРЯДОЧИТЬ ПО Выручка УБЫВ ПЕРВЫЕ 10"
        )
        r = QueryValidationGuardrails.validate(q, {"ДатаНач": "2026-01-01", "ДатаКон": "2026-06-30"})
        assert r.is_valid is True

    def test_english_select(self):
        r = QueryValidationGuardrails.validate("SELECT name FROM Catalog.Nomenclature")
        assert r.is_valid is True

    def test_comment_block(self):
        q = "ВЫБРАТЬ 1 /* комментарий */ ИЗ Справочник.Номенклатура"
        r = QueryValidationGuardrails.validate(q)
        assert r.is_valid is False


class TestValidator:
    @pytest.mark.asyncio
    async def test_local_validation_invalid(self):
        v = QueryValidator()
        r = await v.validate("УДАЛИТЬ ИЗ Справочник.Номенклатура", skip_remote=True)
        assert r.is_valid is False

    @pytest.mark.asyncio
    async def test_local_validation_valid(self):
        v = QueryValidator()
        r = await v.validate("ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура", skip_remote=True)
        assert r.is_valid is True

    @pytest.mark.asyncio
    async def test_remote_fallback(self):
        """Если 1С недоступен — возвращаем is_valid=True с предупреждением"""
        v = QueryValidator()
        r = await v.validate("ВЫБРАТЬ 1")
        # Должен вернуть True (fallback), но с предупреждением
        assert r.is_valid is True
        assert r.error is not None
        assert "не удалось" in r.error.lower()


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_flow_with_mock(self):
        """Тест с мок-клиентом 1С"""
        class MockC1:
            async def post(self, path, json, timeout):
                class Resp:
                    def json(self):
                        return {"is_valid": True}
                return Resp()

        v = QueryValidator(c1_client=MockC1())
        r = await v.validate("ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура")
        assert r.is_valid is True

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Проверка кэширования"""
        class MockCache:
            def __init__(self):
                self.data = {}
            async def get(self, key):
                return self.data.get(key)
            async def set(self, key, value, ttl):
                self.data[key] = value

        class MockC1:
            call_count = 0
            async def post(self, path, json, timeout):
                MockC1.call_count += 1
                class Resp:
                    def json(self):
                        return {"is_valid": True}
                return Resp()

        cache = MockCache()
        v = QueryValidator(c1_client=MockC1(), cache=cache)
        await v.validate("ВЫБРАТЬ 1")
        await v.validate("ВЫБРАТЬ 1")
        # Должен быть только 1 вызов к 1С (второй из кэша)
        assert MockC1.call_count <= 1
