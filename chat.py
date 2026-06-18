#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys

from src.config import settings
from src.deepseek_client import DeepSeekClient
from src.logger import logger


async def main() -> None:
    settings.validate()

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not query:
        print("Использование: python chat.py \"<ваш запрос>\"")
        print()
        print("Примеры запросов:")
        print("  python chat.py \"Покажи топ-5 товаров на складе в Москве, которые не продавались 30 дней\"")
        print("  python chat.py \"Какая выручка за последнюю неделю по менеджеру Иванов?\"")
        print("  python chat.py \"Сколько единиц товара 'Гвоздь 100мм' на всех складах?\"")
        print("  python chat.py \"Кто из клиентов задолжал больше 100 000 рублей?\"")
        return

    logger.info("Запрос пользователя: {}", query)
    print(f"\n🔍 Запрос: {query}\n")

    client = DeepSeekClient()
    result = await client.process_query(query)

    print("=" * 60)
    print("📋 Итоговый ответ:")
    print("=" * 60)
    print()
    print(result["answer"])
    print()

    if result["tool_calls"]:
        print("=" * 60)
        print("🤖 Какие инструменты вызывал AI:")
        print("=" * 60)
        for tc in result["tool_calls"]:
            print(f"  • {tc['name']}({tc['args']})")
        print()

    usage = result["usage"]
    cost = (usage["prompt_tokens"] * 0.00000027 + usage["completion_tokens"] * 0.0011) / 1000000 * 100
    print(f"💰 Токены: {usage['prompt_tokens']} in / {usage['completion_tokens']} out, ~${cost:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
