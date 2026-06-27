from __future__ import annotations

from src.anonymization.models import SensitiveDataType
from src.anonymization.storage import get_or_create_token, init_db, get_stats
from src.anonymization.anonymizer import anonymizer


class TestAnonymization:
    def setup_method(self):
        init_db()

    def test_create_token(self):
        token = get_or_create_token("Иванов Иван", SensitiveDataType.PERSON, "user1")
        assert token.startswith("[ПЕРС-")
        assert token.endswith("]")

    def test_same_value_same_token(self):
        t1 = get_or_create_token("Иванов Иван", SensitiveDataType.PERSON, "user1")
        t2 = get_or_create_token("Иванов Иван", SensitiveDataType.PERSON, "user1")
        assert t1 == t2

    def test_different_values_different_tokens(self):
        t1 = get_or_create_token("Иванов", SensitiveDataType.PERSON, "u1")
        t2 = get_or_create_token("Петров", SensitiveDataType.PERSON, "u1")
        assert t1 != t2

    def test_token_format(self):
        token = get_or_create_token("Тел: 123", SensitiveDataType.CONTACT, "u1")
        assert "[КОНТ-" in token

    def test_anonymize_single_dict(self):
        data = {"name": "Иван", "client_name": "Петров", "age": 30}
        result, ctx = anonymizer.anonymize(data, "user1")
        assert isinstance(result, dict)
        assert result["name"] == "Иван"
        assert "[ПЕРС-" in result["client_name"]
        assert result["age"] == 30

    def test_anonymize_list(self):
        data = [{"client_name": "Иван"}, {"client_name": "Петр"}]
        result, ctx = anonymizer.anonymize(data, "user1")
        assert len(result) == 2
        assert "[ПЕРС-" in result[0]["client_name"]

    def test_stats(self):
        get_or_create_token("Тест", SensitiveDataType.PERSON, "u1")
        get_or_create_token("ООО Ромашка", SensitiveDataType.ORGANIZATION, "u1")
        stats = get_stats()
        assert stats["total_tokens"] >= 2
