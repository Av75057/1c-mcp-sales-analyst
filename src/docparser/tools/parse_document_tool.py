from __future__ import annotations

import base64
from typing import Any

from src.docparser.engine import DocParserEngine
from src.logger import logger

PARSE_DOCUMENT_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "parse_document",
        "description": "Распознать первичный документ (накладную, счёт, УПД) из фото или скана. Извлекает данные в структурированном JSON.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_base64": {
                    "type": "string",
                    "description": "Файл изображения или PDF в base64",
                },
                "filename": {
                    "type": "string",
                    "description": "Имя файла (с расширением)",
                },
                "match_nomenclature": {
                    "type": "boolean",
                    "description": "Сопоставлять номенклатуру со справочником (default: false)",
                },
            },
            "required": ["file_base64", "filename"],
        },
    },
}


async def parse_document_tool(
    file_base64: str,
    filename: str,
    match_nomenclature: bool = False,
) -> dict[str, Any]:
    logger.info("parse_document: {}", filename)
    try:
        data = base64.b64decode(file_base64)
    except Exception as e:
        return {"error": f"Не удалось декодировать файл: {e}"}

    engine = DocParserEngine()

    if match_nomenclature:
        from src.clients.mock_c1_client import MockC1Client
        mock = MockC1Client()
        items = await mock.list_nomenclature("", limit=50)
        catalog = [{"id": i["ref"], "name": i["name"]} for i in items]
        result = await engine.parse_with_matching(filename, data, nomenclature_catalog=catalog)
    else:
        result = await engine.parse(filename, data)

    return result
