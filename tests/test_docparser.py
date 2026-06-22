from __future__ import annotations

import pytest

from src.docparser.matching.nomenclature_matcher import match_nomenclature, match_counterparty
from src.docparser.validation.document_validator import validate_document
from src.docparser.ingestion.file_handler import validate_file


def test_validate_file_jpeg():
    r = validate_file("test.jpg", b"fake_image_data")
    assert r["valid"] is True


def test_validate_file_pdf():
    r = validate_file("test.pdf", b"fake_pdf_data")
    assert r["valid"] is True


def test_validate_file_invalid_ext():
    r = validate_file("test.exe", b"data")
    assert r["valid"] is False


def test_validate_file_too_large():
    r = validate_file("test.jpg", b"x" * 30_000_000)
    assert r["valid"] is False


def test_match_nomenclature_exact():
    catalog = [{"id": "1", "name": "Гвоздь 100мм"}]
    r = match_nomenclature("Гвоздь 100мм", catalog)
    assert r["confidence"] >= 0.9


def test_match_nomenclature_partial():
    catalog = [{"id": "1", "name": "Гвоздь 100мм (упак)"}, {"id": "2", "name": "Саморез 50мм"}]
    r = match_nomenclature("Гвоздь 100мм", catalog)
    assert r["confidence"] >= 0.7


def test_match_nomenclature_no_match():
    catalog = [{"id": "1", "name": "Болт"}]
    r = match_nomenclature("Гвоздь 100мм", catalog)
    assert r["id"] is None


def test_match_counterparty():
    catalog = [{"id": "1", "name": "ООО Метизы"}, {"id": "2", "name": "ООО СтройДом"}]
    r = match_counterparty("ООО Метизы", catalog)
    assert r["id"] == "1"


def test_validate_valid_document():
    doc = {
        "doc_type": "supplier_invoice",
        "header": {"counterparty": "ООО Тест", "date": "2026-06-01", "number": "123"},
        "items": [{"name": "Товар", "quantity": 10, "price": 100, "sum_without_vat": 1000, "vat_rate": 20, "vat_sum": 200, "sum_with_vat": 1200}],
        "totals": {"subtotal": 1000, "vat_total": 200, "total": 1200},
        "confidence": 0.9,
    }
    r = validate_document(doc)
    assert r["is_valid"] is True


def test_validate_wrong_total():
    doc = {
        "doc_type": "supplier_invoice",
        "header": {"counterparty": "ООО Тест", "date": "2026-06-01"},
        "items": [{"name": "Товар", "quantity": 10, "price": 100, "sum_without_vat": 1000, "vat_sum": 0, "sum_with_vat": 1000}],
        "totals": {"subtotal": 1000, "vat_total": 0, "total": 9999},
        "confidence": 0.9,
    }
    r = validate_document(doc)
    assert r["is_valid"] is False


def test_validate_future_date():
    doc = {
        "doc_type": "supplier_invoice",
        "header": {"counterparty": "ООО Тест", "date": "2099-01-01"},
        "items": [],
        "totals": {},
        "confidence": 0.5,
    }
    r = validate_document(doc)
    assert len(r["warnings"]) > 0
