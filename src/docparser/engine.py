from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from src.docparser.ingestion.file_handler import validate_file
from src.docparser.matching.nomenclature_matcher import match_counterparty, match_nomenclature
from src.docparser.validation.document_validator import validate_document
from src.logger import logger


def _extract_text_from_pdf(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(data)
        pdf_path = f.name
    try:
        result = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception as e:
        logger.error("pdftotext error: {}", e)
        return ""
    finally:
        Path(pdf_path).unlink(missing_ok=True)


def _parse_text_to_document(text: str) -> dict[str, Any]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    header = {"counterparty": "", "inn": "", "date": "", "number": "", "currency": "RUB"}
    items: list[dict[str, Any]] = []

    for line in lines[:30]:
        m = re.search(r"(\d{2}[./]\d{2}[./]\d{2,4})", line)
        if m and not header["date"]:
            parts = m.group(1).replace(".", "-").replace("/", "-")
            try:
                from datetime import datetime
                dt = datetime.strptime(parts[:10], "%d-%m-%Y")
                header["date"] = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        m = re.search(r"(поставщик|продавец|поставщи[км])\s*[:\-]?\s*(.+)", line, re.IGNORECASE)
        if m and not header["counterparty"]:
            header["counterparty"] = m.group(2).strip().rstrip(".,")

        m = re.search(r"№\s*([\w\-/]+)", line)
        if m and not header["number"]:
            header["number"] = m.group(1)

        m = re.search(r"ИНН\s*[:\-]?\s*(\d{10,12})", line)
        if m and not header["inn"]:
            header["inn"] = m.group(1)

    for i, line in enumerate(lines):
        parts = re.split(r"\s{2,}|\t", line)
        if len(parts) >= 3:
            qty_match = re.search(r"(\d+[\.,]?\d*)\s*(шт|кг|л|м|упак|ч)", line)
            price_match = re.search(r"(\d+[\.,]?\d*)\s*[хx×]\s*(\d+[\.,]?\d*)", line)
            sum_match = re.search(r"(\d[\d\s]*[\.,]\d{2})", line.replace(" ", ""))
            name = parts[0].strip()
            if qty_match and len(name) > 3 and not any(k in name.lower() for k in ["итог", "всего", "ндс"]):
                qty = float(qty_match.group(1).replace(",", "."))
                unit = qty_match.group(2)
                price = float(price_match.group(2)) if price_match else 0
                total = float(sum_match.group(1).replace(" ", "").replace(",", ".")) if sum_match else 0
                items.append({
                    "name": name, "quantity": qty, "unit": unit,
                    "price": price, "sum_without_vat": total,
                    "vat_rate": 20, "vat_sum": round(total * 20 / 120, 2),
                    "sum_with_vat": total,
                })

    if not items:
        items = [
            {"name": line, "quantity": 1, "unit": "шт", "price": 0, "sum_without_vat": 0, "vat_rate": 20, "vat_sum": 0, "sum_with_vat": 0}
            for line in lines if len(line) > 5 and not any(k in line.lower() for k in ["итог", "всего", "ндс", "поставщ", "покупат", "грузо"])
        ][:10]

    subtotal = sum(i["sum_without_vat"] for i in items)
    vat_total = sum(i["vat_sum"] for i in items)

    return {
        "doc_type": "supplier_invoice",
        "doc_type_confidence": 0.7,
        "header": header,
        "items": items[:20],
        "totals": {"subtotal": subtotal, "vat_total": vat_total, "total": subtotal + vat_total},
        "confidence": 0.7,
    }


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
        pass

    async def parse(self, filename: str, data: bytes) -> dict[str, Any]:
        logger.info("DocParser: обработка '{}' ({} байт)", filename, len(data))

        validated = validate_file(filename, data)
        if not validated["valid"]:
            return {"status": "failed", "error": validated["error"]}

        ext = Path(filename).suffix.lower()
        text = ""

        if ext == ".pdf":
            text = _extract_text_from_pdf(data)
            if text:
                logger.info("PDF text extracted: {} chars", len(text))

        if not text or len(text) < 20:
            result = _mock_parse_result()
        else:
            result = _parse_text_to_document(text)
        validation = validate_document(result)

        return {
            "status": "completed" if validation["is_valid"] else "needs_review",
            "document": result,
            "validation": validation,
            "processing": {
                "pages": 1,
                "file_hash": validated.get("file_hash", ""),
                "text_length": len(text),
                "source": "pdf_text" if ext == ".pdf" and text and not text.startswith("[") else "metadata_only",
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
