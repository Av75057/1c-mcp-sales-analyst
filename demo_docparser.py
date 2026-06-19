#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os

os.environ["USE_MOCK_DATA"] = "true"

from src.docparser.engine import DocParserEngine
from src.docparser.ingestion.file_handler import preprocess_image, validate_file
from src.docparser.matching.nomenclature_matcher import match_nomenclature
from src.docparser.validation.document_validator import validate_document


def generate_test_invoice() -> bytes:
    """Генерируем тестовую накладную как изображение с помощью Pillow"""
    from PIL import Image, ImageDraw, ImageFont
    import io

    img = Image.new("RGB", (800, 1100), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except (OSError, IOError):
        font = ImageFont.load_default()
        font_bold = font

    y = 20
    draw.text((30, y), "ТОВАРНАЯ НАКЛАДНАЯ №147-НС", font=font_bold, fill="black")
    y += 30
    draw.text((30, y), "Дата: 18.06.2026", font=font, fill="black")
    y += 25
    draw.text((30, y), "Поставщик: ООО \"Метизы\"", font=font, fill="black")
    y += 25
    draw.text((30, y), "ИНН: 7712345678", font=font, fill="black")
    y += 25
    draw.text((30, y), "Грузополучатель: ООО \"СтройДом\"", font=font, fill="black")
    y += 40

    headers = ["№", "Наименование", "Кол-во", "Ед.", "Цена", "Сумма"]
    cols = [30, 70, 400, 470, 520, 620]
    for i, h in enumerate(headers):
        draw.text((cols[i], y), h, font=font_bold, fill="black")
    y += 5
    draw.line([(30, y), (780, y)], fill="gray")
    y += 15

    items = [
        ("1", "Гвоздь 100мм", "100", "шт", "12.50", "1 250.00"),
        ("2", "Саморез 3,5х45", "500", "шт", "3.20", "1 600.00"),
        ("3", "Болт М8х30 DIN933", "200", "шт", "8.50", "1 700.00"),
        ("4", "Гайка М8 корончатая", "200", "шт", "4.20", "840.00"),
        ("5", "Шайба 8мм плоская", "400", "шт", "1.50", "600.00"),
        ("6", "Полотенце махровое белое 50Х100", "50", "шт", "180.00", "9 000.00"),
        ("7", "Краска акриловая 5кг", "30", "шт", "450.00", "13 500.00"),
    ]

    for item in items:
        for i, val in enumerate(item):
            draw.text((cols[i], y), val, font=font, fill="black")
        y += 22

    draw.line([(30, y), (780, y)], fill="gray")
    y += 15
    draw.text((30, y), "Итого:", font=font_bold, fill="black")
    y += 25
    draw.text((30, y), "Всего без НДС: 28 490.00", font=font, fill="black")
    y += 20
    draw.text((30, y), "НДС 20%: 5 698.00", font=font, fill="black")
    y += 20
    draw.text((30, y), "Всего с НДС: 34 188.00", font=font_bold, fill="black")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


async def main() -> None:
    print("=" * 60)
    print("📄 AI DocParser — Демо")
    print("=" * 60)

    print("\n📝 Шаг 1: Генерация тестовой накладной...")
    invoice_bytes = generate_test_invoice()
    print(f"   Размер: {len(invoice_bytes)} байт")

    print("\n✅ Шаг 2: Валидация файла...")
    validated = validate_file("invoice.jpg", invoice_bytes)
    print(f"   Валидный: {validated['valid']}")

    print("\n✅ Шаг 3: Предобработка изображения...")
    processed = preprocess_image(invoice_bytes)
    print(f"   Размер после обработки: {len(processed)} байт")

    print("\n🤖 Шаг 4: Распознавание через Vision LLM...")
    engine = DocParserEngine()
    result = await engine.parse("invoice.jpg", invoice_bytes)

    if result["status"] == "failed":
        print(f"\n❌ Ошибка: {result['error']}")
        print("   (Для работы требуется DeepSeek API key в .env)")
        print("\n--- Демо с эмуляцией распознавания ---")

        mock_result = {
            "doc_type": "supplier_invoice",
            "doc_type_confidence": 0.95,
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
                {"name": "Гайка М8 корончатая", "quantity": 200, "unit": "шт", "price": 4.20, "sum_without_vat": 840.00, "vat_rate": 20, "vat_sum": 168.00, "sum_with_vat": 1008.00},
                {"name": "Шайба 8мм плоская", "quantity": 400, "unit": "шт", "price": 1.50, "sum_without_vat": 600.00, "vat_rate": 20, "vat_sum": 120.00, "sum_with_vat": 720.00},
                {"name": "Краска акриловая 5кг", "quantity": 30, "unit": "шт", "price": 450.00, "sum_without_vat": 13500.00, "vat_rate": 20, "vat_sum": 2700.00, "sum_with_vat": 16200.00},
            ],
            "totals": {"subtotal": 28490.00, "vat_total": 5698.00, "total": 34188.00},
            "confidence": 0.92,
        }

        print("\n📄 РЕЗУЛЬТАТ РАСПОЗНАВАНИЯ:")
        print(f"   Тип: {mock_result['doc_type']}")
        print(f"   Поставщик: {mock_result['header']['counterparty']}")
        print(f"   Датa: {mock_result['header']['date']}  Номер: {mock_result['header']['number']}")
        print(f"   Позиций: {len(mock_result['items'])}")

        validation = validate_document(mock_result)
        print(f"\n✅ ВАЛИДАЦИЯ:")
        print(f"   Ошибок: {len(validation['errors'])}")
        print(f"   Предупреждений: {len(validation['warnings'])}")
        print(f"   Суммы сходятся: {validation['totals_match']}")

        print(f"\n📦 СОПОСТАВЛЕНИЕ НОМЕНКЛАТУРЫ:")
        catalog = [
            {"id": "NG-001", "name": "Гвоздь 100мм (упак)"},
            {"id": "NG-002", "name": "Гвоздь 80мм (упак)"},
            {"id": "SR-001", "name": "Саморез 3,5x45мм"},
            {"id": "BT-001", "name": "Болт М8x30 (DIN933)"},
            {"id": "GK-001", "name": "Гайка М8 корончатая"},
            {"id": "SB-001", "name": "Шайба 8мм (плоская)"},
            {"id": "KR-001", "name": "Краска акриловая 5кг"},
            {"id": "PL-001", "name": "Полотенце махровое 50x100"},
        ]
        for item in mock_result["items"]:
            match = match_nomenclature(item["name"], catalog)
            status = "✅" if match["confidence"] >= 0.75 else "⚠️" if match["confidence"] >= 0.6 else "❌"
            print(f"   {status} {item['name'][:25]:25s} → {match['name'][:25]:25s} [{match['confidence']:.0%}]")

        print(f"\n{'=' * 60}")
        print("✅ Демо завершено (режим эмуляции)")
        print("📌 Для работы с реальным API: добавьте DEEPSEEK_API_KEY в .env")
        return

    print(f"\n📄 РЕЗУЛЬТАТ РАСПОЗНАВАНИЯ:")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:1000])


if __name__ == "__main__":
    asyncio.run(main())
