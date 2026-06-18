from __future__ import annotations

import asyncio
import sys

from src.config import settings
from src.logger import logger


def run_chat() -> None:
    import asyncio

    from src.deepseek_client import DeepSeekClient

    settings.validate()
    query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    if not query:
        print("Использование: python -m src chat \"<запрос>\"")
        print()
        print("Примеры запросов:")
        print("  python -m src chat \"Покажи топ-5 товаров на складе в Москве, которые не продавались 30 дней\"")
        print("  python -m src chat \"Какая выручка за последнюю неделю по менеджеру Иванов?\"")
        return

    async def _run():
        logger.info("Запрос пользователя: {}", query)
        client = DeepSeekClient()
        result = await client.process_query(query)

        print(result["answer"])
        print()

        if result["tool_calls"]:
            print("--- Вызванные инструменты ---")
            for tc in result["tool_calls"]:
                print(f"  • {tc['name']}({tc['args']})")

        usage = result["usage"]
        cost_usd = usage["prompt_tokens"] * 0.00000027 + usage["completion_tokens"] * 0.0011
        print(f"\n💰 {usage['prompt_tokens']} in / {usage['completion_tokens']} out, ${cost_usd:.6f}")

    asyncio.run(_run())


def run_server() -> None:
    import asyncio

    from src.server import run_server_stdio

    settings.validate()
    logger.info("Запуск MCP сервера (stdio)")

    async def _run():
        await run_server_stdio()

    asyncio.run(_run())


def run_proxy() -> None:
    settings.validate()
    logger.info("Запуск OpenAI-совместимого прокси на порту {}", settings.mcp_port)
    from src.proxy_server import run

    run()


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python -m src chat \"<запрос>\"")
        print("  python -m src server")
        print("  python -m src proxy")
        return

    mode = sys.argv[1]
    if mode == "chat":
        run_chat()
    elif mode == "server":
        run_server()
    elif mode == "proxy":
        run_proxy()
    else:
        print(f"Неизвестный режим: {mode}. Используйте 'chat', 'server' или 'proxy'")


if __name__ == "__main__":
    main()
