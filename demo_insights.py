#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json

import os
os.environ["USE_MOCK_DATA"] = "true"

from src.config import settings
from src.insights.detectors.sales_anomaly import SalesAnomalyDetector
from src.insights.detectors.sales_growth import SalesGrowthDetector
from src.insights.detectors.stock_shortage import StockShortageDetector
from src.insights.detectors.inactive_clients import InactiveClientsDetector
from src.insights.detectors.receivables_alert import ReceivablesAlertDetector
from src.insights.interpreter.llm_interpreter import LLMInterpreter
from src.insights.models import RawInsight, TenantInsightsConfig


async def main() -> None:
    settings.validate()
    config = TenantInsightsConfig()
    config.stock_days_threshold = 999  # force all items to trigger
    config.sales_drop_threshold = 0.0  # detect any drop

    print("=" * 60)
    print("🤖 AI Insights — Демо")
    print("=" * 60)

    detectors = [
        ("SalesAnomalyDetector", SalesAnomalyDetector(config)),
        ("SalesGrowthDetector", SalesGrowthDetector(config)),
        ("StockShortageDetector", StockShortageDetector(config)),
        ("InactiveClientsDetector", InactiveClientsDetector(config)),
        ("ReceivablesAlertDetector", ReceivablesAlertDetector(config)),
    ]

    all_raws: list[RawInsight] = []
    for name, detector in detectors:
        print(f"\n📡 {name}...")
        insights = await detector.detect()
        if insights:
            print(f"   Найдено {len(insights)} инсайтов:")
            for ins in insights[:3]:
                print(f"   [{ins.priority.value}] {ins.title} ({ins.metric_delta_percent:+.1f}%)")
            all_raws.extend(insights)
        else:
            print(f"   Нет инсайтов")

    if not all_raws:
        print("\n❌ Нет инсайтов для интерпретации")
        return

    print(f"\n{'=' * 60}")
    print(f"🧠 LLM-интерпретация ({len(all_raws)} инсайтов)")
    print(f"{'=' * 60}")

    interpreter = LLMInterpreter()
    processed = await interpreter.interpret_batch(all_raws[:2])

    for p in processed:
        print(f"\n{'─' * 50}")
        print(f"📌 {p.llm_title}")
        print(f"{'─' * 50}")
        print(f"📝 {p.llm_summary}")
        print(f"🔍 Гипотеза: {p.llm_hypothesis}")
        if p.llm_recommendations:
            print(f"💡 Рекомендации:")
            for r in p.llm_recommendations:
                print(f"   • {r}")
        print(f"\n📨 Сообщение:\n{p.formatted_message}")

    print(f"\n{'=' * 60}")
    print("✅ Демо завершено")
    print(f"   Всего сырых инсайтов: {len(all_raws)}")
    print(f"   Интерпретировано: {len(processed)}")


if __name__ == "__main__":
    asyncio.run(main())
