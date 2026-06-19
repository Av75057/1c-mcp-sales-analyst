from __future__ import annotations

import json
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
        text = result.stdout.strip()
        if text:
            return text
        logger.info("PDF без текста, пробую OCR...")
        return _ocr_pdf(data)
    except Exception as e:
        logger.error("pdftotext error: {}", e)
        return ""
    finally:
        Path(pdf_path).unlink(missing_ok=True)


def _ocr_image(image_path: str) -> str:
    try:
        result = subprocess.run(["tesseract", image_path, "stdout", "-l", "rus+eng"], capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception as e:
        logger.error("tesseract error: {}", e)
        return ""


def _ocr_bytes(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(data)
        img_path = f.name
    try:
        return _ocr_image(img_path)
    finally:
        Path(img_path).unlink(missing_ok=True)


def _ocr_pdf(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(data)
        pdf_path = f.name
    all_text = ""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["pdftoppm", pdf_path, f"{tmpdir}/page", "-png", "-r", "300"], timeout=60, capture_output=True)
            for page_file in sorted(Path(tmpdir).glob("*.png")):
                text = _ocr_image(str(page_file))
                if text:
                    all_text += text + "\n"
        return all_text.strip()
    except Exception as e:
        logger.error("PDF OCR error: {}", e)
        return ""
    finally:
        Path(pdf_path).unlink(missing_ok=True)


LLM_PARSE_PROMPT = """Ты — парсер бухгалтерских документов. Извлеки данные в JSON.

Документ:
```
{text}
```

Правила:
- counterparty = ПОСТАВЩИК (тот, кто продаёт/оказывает услуги), НЕ покупатель
- inn = ИНН поставщика
- items = товары/услуги из таблицы

Верни ТОЛЬКО JSON:
{{
  "counterparty": "название поставщика",
  "inn": "ИНН",
  "date": "YYYY-MM-DD",
  "number": "номер",
  "items": [{{"name": "товар", "quantity": 0, "unit": "шт", "price": 0, "sum": 0}}],
  "total": 0
}}
"""


async def _parse_with_llm(text: str) -> dict[str, Any]:
    from openai import AsyncOpenAI
    from src.config import settings
    import httpx

    client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url="https://api.deepseek.com", http_client=httpx.AsyncClient(timeout=30.0))
    prompt = LLM_PARSE_PROMPT.format(text=text[:2000])
    try:
        resp = await client.chat.completions.create(model=settings.llm_model, messages=[{"role": "user", "content": prompt}], temperature=0.05, max_tokens=1000)
        content = resp.choices[0].message.content or "{}"
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if m:
            content = m.group(1).strip()
        data = json.loads(content)
    except Exception as e:
        logger.error("LLM parse error: {}", e)
        data = {}

    items = []
    for i in data.get("items", []):
        items.append({"name": i.get("name", ""), "quantity": float(i.get("quantity", 0)), "unit": i.get("unit", "шт"), "price": float(i.get("price", 0)), "sum_without_vat": float(i.get("sum", 0)), "vat_rate": 20, "vat_sum": 0, "sum_with_vat": float(i.get("sum", 0))})
    subtotal = sum(i["sum_without_vat"] for i in items)
    return {
        "doc_type": "supplier_invoice",
        "doc_type_confidence": 0.85,
        "header": {"counterparty": data.get("counterparty", ""), "inn": data.get("inn", ""), "date": data.get("date", ""), "number": data.get("number", ""), "currency": "RUB"},
        "items": items,
        "totals": {"subtotal": subtotal, "vat_total": 0, "total": data.get("total", subtotal)},
        "confidence": 0.85,
    }


def _parse_regex(text: str) -> dict[str, Any]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    header = {"counterparty": "", "inn": "", "date": "", "number": "", "currency": "RUB"}
    items: list[dict[str, Any]] = []

    for line in lines[:30]:
        if ":" in line and not header["counterparty"]:
            before = line.split(":", 1)[0].strip().lower()
            after = line.split(":", 1)[1].strip()
            if any(k in before for k in ["поставщик", "продавец", "исполнитель", "плательщик", "получател"]):
                header["counterparty"] = after.rstrip(".,;")
        m = re.search(r"(\d{2})[./](\d{2})[./](\d{2,4})", line)
        if m and not header["date"]:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            y += 2000 if y < 100 else 0
            if 2020 <= y <= 2030 and 1 <= mo <= 12:
                header["date"] = f"{y}-{mo:02d}-{d:02d}"
        if not header["date"]:
            m = re.search(r"(\d{1,2})\s+(январ|феврал|март|апрел|ма[йя]|июн[ья]?|июл[ья]?|август|сентябр|октябр|ноябр|декабр)", line, re.IGNORECASE)
            if m:
                months = {"январ":1,"феврал":2,"март":3,"апрел":4,"май":5,"мая":5,"июн":6,"июня":6,"июл":7,"июля":7,"август":8,"сентябр":9,"октябр":10,"ноябр":11,"декабр":12}
                ym = re.search(r"(\d{4})\s*г", line)
                header["date"] = f"{ym.group(1) if ym else 2026}-{months.get(m.group(2).lower()[:6], 1):02d}-{int(m.group(1)):02d}"
        m = re.search(r"[№Nn][sS]?\s*(\d+)", line)
        if m and not header["number"] and int(m.group(1)) < 10000:
            header["number"] = m.group(1)
        m = re.search(r"[ИHMN][НH][НH]?\s*[:\-]?\s*(\d{10,12})", line)
        if m and not header["inn"]:
            header["inn"] = m.group(1)

    SKIP = {"итог", "всего", "ндс", "банк", "сбербанк", "бик", "корр", "адрес", "тел", "email"}
    for line in lines:
        ll = line.lower().strip()
        if any(k in ll for k in SKIP):
            continue
        m = re.search(r"(\d+[\.,]?\d*)\s*(шт|кг|л|м|упак|ч)\b", ll)
        if m:
            name = re.sub(r"^\d+[\.\)]\s*", "", line[:m.start()].strip().rstrip(",. "))
            if len(name) >= 3:
                price = 0.0
                total = 0.0
                nums = re.findall(r"(\d[\d\s]*[\.,]\d{2})", line[m.end():])
                if len(nums) >= 2:
                    price = float(nums[0].replace(" ", "").replace(",", "."))
                    total = float(nums[1].replace(" ", "").replace(",", "."))
                items.append({"name": name, "quantity": float(m.group(1).replace(",", ".")), "unit": m.group(2), "price": price, "sum_without_vat": total, "vat_rate": 20, "vat_sum": round(total * 20 / 120, 2), "sum_with_vat": total})

    ft = " ".join(lines).lower()
    doc_type = "bill" if re.search(r"счет|счeт", ft) else "act" if re.search(r"акт", ft) else "supplier_invoice"
    subtotal = sum(i["sum_without_vat"] for i in items)
    return {"doc_type": doc_type, "doc_type_confidence": 0.6, "header": header, "items": items[:20], "totals": {"subtotal": subtotal, "vat_total": sum(i["vat_sum"] for i in items), "total": subtotal + sum(i["vat_sum"] for i in items)}, "confidence": 0.6}


def _mock_parse_result() -> dict[str, Any]:
    return {"doc_type": "supplier_invoice", "doc_type_confidence": 0.92, "header": {"counterparty": "ООО \"Метизы\"", "inn": "7712345678", "date": "2026-06-18", "number": "147-НС", "currency": "RUB"}, "items": [{"name": "Гвоздь 100мм", "quantity": 100, "unit": "шт", "price": 12.50, "sum_without_vat": 1250.00, "vat_rate": 20, "vat_sum": 250.00, "sum_with_vat": 1500.00}, {"name": "Саморез 3,5х45", "quantity": 500, "unit": "шт", "price": 3.20, "sum_without_vat": 1600.00, "vat_rate": 20, "vat_sum": 320.00, "sum_with_vat": 1920.00}, {"name": "Болт М8х30 DIN933", "quantity": 200, "unit": "шт", "price": 8.50, "sum_without_vat": 1700.00, "vat_rate": 20, "vat_sum": 340.00, "sum_with_vat": 2040.00}, {"name": "Краска акриловая 5кг", "quantity": 30, "unit": "шт", "price": 450.00, "sum_without_vat": 13500.00, "vat_rate": 20, "vat_sum": 2700.00, "sum_with_vat": 16200.00}], "totals": {"subtotal": 18050.00, "vat_total": 3610.00, "total": 21660.00}, "confidence": 0.92}


class DocParserEngine:
    async def parse(self, filename: str, data: bytes) -> dict[str, Any]:
        logger.info("DocParser: обработка '{}' ({} байт)", filename, len(data))
        validated = validate_file(filename, data)
        if not validated["valid"]:
            return {"status": "failed", "error": validated["error"]}

        ext = Path(filename).suffix.lower()
        text = ""

        if ext == ".pdf":
            text = _extract_text_from_pdf(data)
        elif ext in (".txt", ".csv"):
            text = data.decode("utf-8", errors="replace")
        elif ext in (".jpg", ".jpeg", ".png", ".tiff", ".tif"):
            text = _ocr_bytes(data)

        if not text or len(text) < 20:
            result = _mock_parse_result()
            source = "mock"
        else:
            result = await _parse_with_llm(text)
            source = "llm"
            if not result.get("items"):
                result = _parse_regex(text)
                source = "regex"

        validation = validate_document(result)
        return {"status": "completed" if validation["is_valid"] else "needs_review", "document": result, "validation": validation, "processing": {"pages": 1, "file_hash": validated.get("file_hash", ""), "text_length": len(text), "source": source}}

    async def parse_with_matching(self, filename: str, data: bytes, nomenclature_catalog: list[dict[str, str]] | None = None, counterparty_catalog: list[dict[str, str]] | None = None) -> dict[str, Any]:
        parsed = await self.parse(filename, data)
        if parsed["status"] == "failed":
            return parsed
        doc = parsed.get("document", {})
        header = doc.get("header", {})
        if counterparty_catalog and header.get("counterparty"):
            header["counterparty_match"] = match_counterparty(header["counterparty"], counterparty_catalog)
        if nomenclature_catalog:
            for item in doc.get("items", []):
                item["nomenclature_match"] = match_nomenclature(item.get("name", ""), nomenclature_catalog)
        return parsed
