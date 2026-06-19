from __future__ import annotations

from typing import Any

from src.docparser.ingestion.file_handler import load_image, validate_file
from src.docparser.matching.nomenclature_matcher import match_counterparty, match_nomenclature
from src.docparser.recognition.vision_client import VisionClient
from src.docparser.validation.document_validator import validate_document
from src.logger import logger


class DocParserEngine:
    def __init__(self) -> None:
        self.vision = VisionClient()

    async def parse(self, filename: str, data: bytes) -> dict[str, Any]:
        logger.info("DocParser: обработка '{}' ({} байт)", filename, len(data))

        validated = validate_file(filename, data)
        if not validated["valid"]:
            return {"status": "failed", "error": validated["error"]}

        images = load_image(filename, data)
        if not images:
            return {"status": "failed", "error": "Не удалось загрузить изображение"}

        result = await self.vision.recognize(images[0])
        if "error" in result:
            return {"status": "failed", "error": result["error"]}

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
