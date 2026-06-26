from __future__ import annotations

from src.data_quality.models.sales import SalesRecord
from src.data_quality.models.stock import StockRecord
from src.data_quality.monitoring.anomaly_detector import detect_anomalies, detect_duplicates, check_business_rules
from src.data_quality.monitoring.dashboard import compute_quality_report
from src.data_quality.validation.decorators import validate_output


class TestSalesRecord:
    def test_valid_record(self):
        r = SalesRecord(date="2026-06-01", nomenclature="Товар", quantity=10, sum=1000)
        assert r.quantity == 10
        assert r.sum == 1000

    def test_negative_quantity_clamped(self):
        r = SalesRecord(quantity=-5, sum=100)
        assert r.quantity == 0

    def test_empty_nomenclature(self):
        from pydantic import ValidationError
        import pytest
        with pytest.raises(ValidationError):
            SalesRecord(nomenclature="", quantity=1, sum=10)

    def test_negative_sum_clamped(self):
        r = SalesRecord(sum=-100)
        assert r.sum == 0

    def test_future_date(self):
        import pytest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SalesRecord(date="1999-01-01", nomenclature="x", quantity=1, sum=1)


class TestStockRecord:
    def test_valid(self):
        r = StockRecord(nomenclature="Товар", quantity=100)
        assert r.quantity == 100

    def test_negative_rejected(self):
        import pytest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            StockRecord(quantity=-10)

    def test_validate_stock(self):
        data = [{"nomenclature": "A", "quantity": 10}, {"nomenclature": "B", "quantity": -5}, {"nomenclature": "", "quantity": 10}]
        result = StockRecord.validate_stock(data)
        assert len(result) >= 1


class TestAnomalyDetector:
    def test_detect(self):
        data = [{"value": 10}] * 20 + [{"value": 1000}]
        anomalies = detect_anomalies(data, "value")
        assert len(anomalies) >= 1
        assert anomalies[0]["value"] == 1000

    def test_no_anomalies(self):
        data = [{"value": 10}] * 10
        assert detect_anomalies(data, "value") == []

    def test_small_dataset(self):
        assert detect_anomalies([{"v": 1}, {"v": 2}], "v") == []


class TestDuplicateDetector:
    def test_detect(self):
        data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "A"}]
        dups = detect_duplicates(data, ["name"])
        assert len(dups) == 1
        assert dups[0]["duplicate_of"] == 0

    def test_no_duplicates(self):
        data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        assert detect_duplicates(data, ["name"]) == []


class TestBusinessRules:
    def test_positive_amount(self):
        data = [{"amount": 100}, {"amount": -50}]
        rules = [{"name": "positive", "check": lambda r: r["amount"] >= 0, "message": "negative"}]
        violations = check_business_rules(data, rules)
        assert len(violations) == 1

    def test_all_valid(self):
        data = [{"amount": 100}, {"amount": 200}]
        rules = [{"name": "positive", "check": lambda r: r["amount"] >= 0, "message": "negative"}]
        assert check_business_rules(data, rules) == []


class TestQualityReport:
    def test_report(self):
        data = [{"nomenclature": "A", "sum": 100}, {"nomenclature": "B", "sum": -50}, {"nomenclature": "", "sum": 200}]
        report = compute_quality_report(data)
        assert report["total_records"] == 3
        assert report["quality_score"] >= 0
