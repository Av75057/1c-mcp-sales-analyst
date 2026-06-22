#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os

os.environ["USE_MOCK_DATA"] = "true"

from src.insights.root_cause import analyze_root_cause


async def main() -> None:
    anomalies = [
        {"detector": "sales_anomaly", "entity_id": "Гвоздь 100мм", "entity_name": "Гвоздь 100мм", "metric_name": "sales_volume", "metric_value": 200, "metric_baseline": 1200, "metric_delta_percent": -83.3, "title": "Падение продаж: Гвоздь 100мм", "detected_at": "2026-06-22"},
        {"detector": "stock_shortage", "entity_id": "Полотенце махровое", "entity_name": "Полотенце махровое", "metric_name": "stock_days", "metric_value": 0.5, "metric_baseline": 7, "metric_delta_percent": -92.9, "title": "Товар заканчивается: Полотенце махровое", "detected_at": "2026-06-22"},
    ]

    for anom in anomalies:
        print(f"\n{'=' * 60}")
        print(f"🔍 {anom['title']}")
        print(f"{'=' * 60}")
        result = await analyze_root_cause(anom)
        print(f"\n📌 Причина: {result.get('root_cause', 'N/A')}")
        print(f"📝 Объяснение: {result.get('explanation', 'N/A')}")
        print(f"🎯 Уверенность: {result.get('confidence', 0):.0%}")
        if result.get("recommendations"):
            print(f"💡 Рекомендации:")
            for r in result["recommendations"]:
                print(f"   • {r}")
        if result.get("factors"):
            print(f"📊 Факторы: {', '.join(result['factors'])}")


if __name__ == "__main__":
    asyncio.run(main())
