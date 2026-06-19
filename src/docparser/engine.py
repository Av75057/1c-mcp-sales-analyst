from __future__ import annotations

from typing import Any

from src.docparser.ingestion.file_handler import load_image, validate_file
from src.docparser.matching.nomenclature_matcher import match_counterparty, match_nomenclature
from src.docparser.recognition.vision_client import VisionClient
from src.docparser.validation.document_validator import validate_document
from src.logger import logger


def _mock_parse_result() -> dict[str, Any]:
    return {
        "doc_type": "supplier_invoice",
        "doc_type_confidence": 0.92,
        "header": {
            "counterparty": "ООО \"Метизы\"",
            "inn": "7712345678",
            "date": "2026-06-18",
            "number": "147-НС",
            "currency": "RUB",
        },
        "items": [
            {"name": "Гвоздь 100мм", "quantity": 100, "unit": "шт", "price": 12.50, "sum_without_vat": 1250.00, "vat_rate": 20, "vat_sum": 250.00, "sum_with_vat": 1500.00},
            {"name": "Саморез 3,5х45", "quantity": 500, "unit": "шт", "price": 3.20, "sum_without_vat": 1600.00, "vat_rate": 20, "vat_sum": 320.00, "sum_with_vat": 1920.00},
            {"name": "Болт М8х30 DIN933", "quantity": 200, "unit": "шт", "price": 8.50, "sum_without_vat": 1700.00, "vat_rate": 20, "vat_sum": 340.00, "sum_with_vat": 2040.00},
            {"name": "Краска акриловая 5кг", "quantity": 30, "unit": "шт", "price": 450.00, "sum_without_vat": 13500.00, "vat_rate": 20, "vat_sum": 2700.00, "sum_with_vat": 16200.00},
        ],
        "totals": {"subtotal": 18050.00, "vat_total": 3610.00, "total": 21660.00},
        "confidence": 0.92,
    }


class DocParserEngine:
    def __init__(self) -> None:
        self.vision = VisionClient()

    async def parse(self, filename: str, data: bytes) -> dict[str, Any]:
        logger.info("DocParser: обработка '{}' ({} байт)", filename, len(data))

        validated = validate_file(filename, data)
        if not validated["valid"]:
            return {"status": "failed", "error": validated["error"]}

        # Используем мок-распознавание (для продакшена нужна Vision API)
        result = _mock_parse_result()

        validation = validate_document(result)

        return {
            "status": "completed" if validation["is_valid"] else "needs_review",
            "document": result,
            "validation": validation,
            "processing": {
                "pages": len(images),
                "file_hash": validated.get("file_hash", ""),
            },
        }

    async def parse_with_matching(
        self,
        filename: str,
        data: bytes,
        nomenclature_catalog: list[dict[str, str]] | None = None,
        counterparty_catalog: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        parsed = await self.parse(filename, data)
        if parsed["status"] == "failed":
            return parsed

        doc = parsed.get("document", {})
        header = doc.get("header", {})

        if counterparty_catalog and header.get("counterparty"):
            match = match_counterparty(header["counterparty"], counterparty_catalog)
            header["counterparty_match"] = match

        if nomenclature_catalog:
            for item in doc.get("items", []):
                match = match_nomenclature(item.get("name", ""), nomenclature_catalog)
                item["nomenclature_match"] = match

        return parsed
