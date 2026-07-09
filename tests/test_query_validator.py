from __future__ import annotations

import os

import pytest
from src.mcp.tools.query_validator import QueryValidationGuardrails, QueryValidator


class TestGuardrails:
    def test_valid_select(self):
        r = QueryValidationGuardrails.validate("ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура")
        assert r.is_valid is True

    def test_empty_query(self):
        r = QueryValidationGuardrails.validate("")
        assert r.is_valid is False

    def test_too_long(self):
        q = "ВЫБРАТЬ " + "Поле, " * 1000
        r = QueryValidationGuardrails.validate(q)
        assert r.is_valid is False

    def test_forbidden_update(self):
        r = QueryValidationGuardrails.validate("ИЗМЕНИТЬ Справочник.Номенклатура")
        assert r.is_valid is False

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

    def test_valid_with_params(self):
        r = QueryValidationGuardrails.validate(
            "ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура ГДЕ Дата > &ДатаНач",
            {"ДатаНач": "2026-01-01"},
        )
        assert r.is_valid is True

    def test_too_many_params(self):
        r = QueryValidationGuardrails.validate("ВЫБРАТЬ 1", {f"p{i}": i for i in range(100)})
        assert r.is_valid is False

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

    def test_forbidden_drop(self):
        r = QueryValidationGuardrails.validate("DROP TABLE Товары")
        assert r.is_valid is False

    def test_forbidden_truncate(self):
        r = QueryValidationGuardrails.validate("TRUNCATE TABLE Товары")
        assert r.is_valid is False

    def test_mixed_russian_english(self):
        r = QueryValidationGuardrails.validate("SELECT * FROM РегистрНакопления.Продажи WHERE Сумма > 1000")
        assert r.is_valid is True

    def test_query_hash_stable(self):
        r1 = QueryValidationGuardrails.validate("ВЫБРАТЬ 1")
        r2 = QueryValidationGuardrails.validate("ВЫБРАТЬ 1")
        assert r1.query_hash == r2.query_hash


class TestValidator:
    @pytest.mark.asyncio
    async def test_local_skip_invalid(self):
        v = QueryValidator()
        r = await v.validate("УДАЛИТЬ ИЗ Справочник.Номенклатура", skip_remote=True)
        assert r.is_valid is False

    @pytest.mark.asyncio
    async def test_local_skip_valid(self):
        v = QueryValidator()
        r = await v.validate("ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура", skip_remote=True)
        assert r.is_valid is True

    @pytest.mark.asyncio
    async def test_remote_fallback(self):
        v = QueryValidator()
        r = await v.validate("ВЫБРАТЬ 1")
        assert r.is_valid is True
        assert r.error is not None


class TestMock:
    @pytest.mark.asyncio
    async def test_mock_valid(self):
        class MockC1:
            async def _request(self, method, path, json):
                class Resp:
                    def json(self):
                        return {"is_valid": True}
                return Resp()

        v = QueryValidator(c1_client=MockC1())
        r = await v.validate("ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура")
        assert r.is_valid is True

    @pytest.mark.asyncio
    async def test_mock_invalid(self):
        class MockC1:
            async def _request(self, method, path, json):
                class Resp:
                    def json(self):
                        return {"is_valid": False, "error": "Bad query"}
                return Resp()

        v = QueryValidator(c1_client=MockC1())
        r = await v.validate("SELECT bad")
        assert r.is_valid is False

    @pytest.mark.asyncio
    async def test_cache(self):
        class MockCache:
            def __init__(self):
                self.data = {}
            async def get(self, key):
                return self.data.get(key)
            async def set(self, key, value, ttl):
                self.data[key] = value

        class MockC1:
            calls = 0
            async def _request(self, method, path, json):
                MockC1.calls += 1
                class Resp:
                    def json(self):
                        return {"is_valid": True}
                return Resp()

        v = QueryValidator(c1_client=MockC1(), cache=MockCache())
        await v.validate("ВЫБРАТЬ 1")
        await v.validate("ВЫБРАТЬ 1")
        assert MockC1.calls <= 1

    @pytest.mark.asyncio
    async def test_mock_rejects_update(self):
        class MockC1:
            async def _request(self, method, path, json):
                q = json.get("query", "")
                is_valid = not ("UPDATE" in q.upper() or "DROP" in q.upper())
                class Resp:
                    def json(self):
                        return {"is_valid": is_valid}
                return Resp()

        v = QueryValidator(c1_client=MockC1())
        r = await v.validate("UPDATE Товары SET Цена = 100")
        assert r.is_valid is False


@pytest.mark.skipif(os.getenv("USE_MOCK_DATA", "true") != "false", reason="Только для реальной 1С")
class TestReal1C:
    @pytest.mark.asyncio
    async def test_valid(self):
        from src.clients.c1_client import C1Client
        v = QueryValidator(c1_client=C1Client())
        r = await v.validate("ВЫБРАТЬ Наименование ИЗ Справочник.Номенклатура")
        assert r.is_valid is True

    @pytest.mark.asyncio
    async def test_invalid_update(self):
        from src.clients.c1_client import C1Client
        v = QueryValidator(c1_client=C1Client())
        r = await v.validate("UPDATE Справочник.Номенклатура SET Наименование = 'Тест'")
        assert r.is_valid is False

    @pytest.mark.asyncio
    async def test_invalid_drop(self):
        from src.clients.c1_client import C1Client
        v = QueryValidator(c1_client=C1Client())
        r = await v.validate("ВЫБРАТЬ 1; DROP TABLE Товары")
        assert r.is_valid is False
