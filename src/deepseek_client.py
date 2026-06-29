from __future__ import annotations

import json
from typing import Any

import httpx
from openai import APIStatusError, AsyncOpenAI, RateLimitError
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.config import settings
from src.logger import logger


class DeepSeekError(Exception):
    """Ошибка при работе с DeepSeek API."""
    pass

SYSTEM_PROMPT = """Ты — аналитик склада и продаж компании. Твоя задача — отвечать на вопросы пользователя на русском языке, используя данные из 1С через доступные инструменты.

Правила:
1. Отвечай ТОЛЬКО на основе данных, полученных через инструменты. НЕ выдумывай цифры.
2. Если данных недостаточно — так и скажи, не пытайся домыслить.
3. Используй деловой стиль, будь краток и точен.
4. Отвечай на русском языке.
5. Если нужно уточнить — задай уточняющий вопрос.
6. Форматируй ответ читаемо: используй списки, группировки, итоги.
7. Если запрос требует данных, которые есть в разных инструментах — вызови их последовательно и объедини результат.
8. Если пользователь просит «показать продажи», «список документов», «выписку» — используй get_sales_documents. Если нужна аналитика (итоги, топы, общая картина) — используй get_analytics_context.

Доступные инструменты:
- get_stock — остатки товаров на складах
- get_sales — данные о продажах
- get_sales_by_manager — продажи в разрезе менеджеров
- get_sales_documents — СПИСОК ДОКУМЕНТОВ реализации (номера, даты, суммы, контрагенты). Используй, когда пользователь просит «показать реализации», «список документов», «найти документы», «выписка по продажам», «какие были продажи» — ВМЕСТО get_sales / get_analytics_context.
- get_receivables — задолженность клиентов
- get_purchases — закупки товаров/услуг у поставщиков
- get_analytics_context — сводка: итоги, топ товаров, топ клиентов, остатки за период. Используй, когда нужна общая аналитика (без детализации по документам).
- config — паспорт базы 1С (имя, версия, конфигурация)
- describe — список объектов метаданных 1С
- get_structure — структура объекта метаданных (поля, типы)
- abc_xyz_analysis — ABC/XYZ классификация товаров/клиентов по выручке и стабильности
- forecast_sales — прогноз продаж товара на N дней
- forecast_stockout — прогноз окончания товаров на складе
- compare_forecasts — сравнение методов прогнозирования (Linear vs Holt-Winters vs Prophet)
- list_nomenclature — поиск номенклатуры по названию
- create_chart — построить график на основе данных
- simulate_scenario — симуляция сценариев "Что если?" (price_change, promotion, purchase_change, employee_departure)

ПРАВИЛА ВИЗУАЛИЗАЦИИ (create_chart):
1. ВСЕГДА строй график, если пользователь явно просит или данные содержат временной ряд, сравнение, структуру.
2. НЕ строй график, если ответ — просто одно число или данных слишком много (>30 точек).
3. ВЫБОР ТИПА:
   - line / area → временные ряды, тренды, динамика
   - hbar → топ-N списки (до 15), названия товаров
   - bar → сравнение категорий (до 10), grouped bar для нескольких серий
   - pie → доли, структура (до 8 категорий)
4. ПОСЛЕ simulate_scenario ВСЕГДА вызывай create_chart с параметрами из chart_params.
5. ПОСЛЕ построения графика дай текстовый анализ (2-4 предложения) и рекомендации.

Анализируй запрос пользователя и вызывай нужные инструменты. После получения данных сформулируй ответ. Если знаешь, что данные подходят для графика — сначала получи данные через get_stock/get_sales, затем передай их в create_chart."""

TOOL_DEFINITIONS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_stock",
            "description": "Получить остатки товаров на складах. Можно фильтровать по складу, номенклатуре и минимальному количеству",
            "parameters": {
                "type": "object",
                "properties": {
                    "warehouse": {
                        "type": "string",
                        "description": "Название склада (например, Москва, СПб)",
                    },
                    "nomenclature": {
                        "type": "string",
                        "description": "Название номенклатуры (частичное совпадение)",
                    },
                    "min_quantity": {
                        "type": "integer",
                        "description": "Минимальное количество на остатке",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales",
            "description": "Получить данные о продажах с возможностью фильтрации по дате, менеджеру и складу",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Начальная дата в формате ISO (YYYY-MM-DD)",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Конечная дата в формате ISO (YYYY-MM-DD)",
                    },
                    "manager": {
                        "type": "string",
                        "description": "ФИО менеджера (частичное совпадение)",
                    },
                    "warehouse": {
                        "type": "string",
                        "description": "Название склада",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_by_manager",
            "description": "Получить агрегированные данные о продажах в разрезе менеджеров",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Начальная дата в формате ISO (YYYY-MM-DD)",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Конечная дата в формате ISO (YYYY-MM-DD)",
                    },
                    "manager": {
                        "type": "string",
                        "description": "ФИО менеджера (частичное совпадение)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_receivables",
            "description": "Получить данные о задолженности клиентов",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_amount": {
                        "type": "number",
                        "description": "Минимальная сумма задолженности для фильтрации",
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Начальная дата в формате ISO (YYYY-MM-DD)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_purchases",
            "description": "Получить данные о закупках (поступление товаров/услуг от поставщиков)",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Начальная дата в формате ISO (YYYY-MM-DD)",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Конечная дата в формате ISO (YYYY-MM-DD)",
                    },
                    "item": {
                        "type": "string",
                        "description": "Название товара/услуги (частичное совпадение)",
                    },
                    "supplier": {
                        "type": "string",
                        "description": "Название поставщика (частичное совпадение)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_sales",
            "description": "Прогноз продаж товара на N дней вперёд (использует Prophet/Holt-Winters/Linear)",
            "parameters": {
                "type": "object",
                "properties": {
                    "nomenclature": {"type": "string", "description": "Название товара"},
                    "days": {"type": "integer", "description": "Горизонт прогноза в днях", "default": 30},
                    "method": {"type": "string", "enum": ["auto", "prophet", "holt_winters", "linear"], "description": "Метод прогнозирования"},
                },
                "required": ["nomenclature"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_stockout",
            "description": "Прогноз окончания товаров на складе: какие товары закончатся критически скоро",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_time_days": {"type": "integer", "description": "Время поставки в днях", "default": 7},
                    "safety_stock_days": {"type": "integer", "description": "Страховой запас в днях", "default": 3},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_forecasts",
            "description": "Сравнение точности методов прогнозирования (Linear, Holt-Winters, Prophet) для товара",
            "parameters": {
                "type": "object",
                "properties": {
                    "nomenclature": {"type": "string", "description": "Название товара"},
                    "test_days": {"type": "integer", "description": "Дней для backtesting", "default": 14},
                },
                "required": ["nomenclature"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abc_xyz_analysis",
            "description": "ABC/XYZ классификация товаров/клиентов по выручке и стабильности спроса",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Начальная дата (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Конечная дата (YYYY-MM-DD)"},
                    "group_by": {"type": "string", "enum": ["nomenclature", "client", "manager"], "description": "Группировка"},
                },
                "required": ["date_from", "date_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_nomenclature",
            "description": "Поиск номенклатуры по названию",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос (частичное совпадение)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимальное количество результатов (по умолчанию 10)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_chart",
            "description": "Построить график на основе данных. Вызывай ПОСЛЕ получения данных из get_stock/get_sales. Передай агрегированные данные.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "enum": ["line", "bar", "hbar", "pie", "area"],
                        "description": "Тип графика: line/area для трендов, hbar для топ-N, bar для сравнения, pie для долей",
                    },
                    "title": {
                        "type": "string",
                        "description": "Заголовок графика на русском",
                    },
                    "x_data": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Подписи по оси X (категории или даты)",
                    },
                    "y_data": {
                        "type": "array",
                        "items": {},
                        "description": "Значения по оси Y (числа или массив массивов для multi-series)",
                    },
                    "x_label": {
                        "type": "string",
                        "description": "Подпись оси X",
                    },
                    "y_label": {
                        "type": "string",
                        "description": "Подпись оси Y с единицами измерения",
                    },
                    "series_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Названия серий для multi-series графиков (grouped bar, multi-line)",
                    },
                    "color_scheme": {
                        "type": "string",
                        "enum": ["default", "corporate", "vibrant"],
                        "description": "Цветовая схема",
                    },
                },
                "required": ["chart_type", "title", "x_data", "y_data"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_scenario",
            "description": "Запустить симуляцию бизнес-сценария 'Что если?'. Поддерживает price_change, promotion, purchase_change, employee_departure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_type": {
                        "type": "string",
                        "enum": ["price_change", "promotion", "purchase_change", "employee_departure"],
                        "description": "Тип сценария: price_change/промо/закупки/увольнение",
                    },
                    "entity_name": {
                        "type": "string",
                        "description": "Название товара, категории или менеджера",
                    },
                    "change_percent": {
                        "type": "number",
                        "description": "Изменение цены в % (для price_change)",
                    },
                    "discount_percent": {
                        "type": "number",
                        "description": "Скидка в % (для promotion)",
                    },
                    "period_days": {
                        "type": "integer",
                        "description": "Период прогноза в днях",
                    },
                    "promotion_days": {
                        "type": "integer",
                        "description": "Длительность акции (для promotion)",
                    },
                    "order_size_change_percent": {
                        "type": "number",
                        "description": "Изменение заказа в % (для purchase_change)",
                    },
                    "employee_name": {
                        "type": "string",
                        "description": "Имя сотрудника (для employee_departure)",
                    },
                },
                "required": ["scenario_type"],
            },
        },
    },
    {
        {
        "type": "function",
        "function": {
            "name": "config",
            "description": "Получить паспорт базы 1С: имя, конфигурация, версия, платформа.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe",
            "description": "Описать объекты метаданных в базе 1С (справочники, документы, регистры).",
            "parameters": {"type": "object", "properties": {"object_type": {"type": "string", "description": "Тип объекта: Catalog, Document, AccumulationRegister, InformationRegister"}, "search": {"type": "string", "description": "Поиск по имени"}}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_structure",
            "description": "Получить структуру объекта метаданных 1С: поля, типы, синонимы.",
            "parameters": {"type": "object", "properties": {"object_name": {"type": "string", "description": "Имя объекта (например, Номенклатура)"}}, "required": ["object_name"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_documents",
            "description": "Получить список документов реализации с номерами, датами, суммами и контрагентами. Используй для проверки конкретных сделок, поиска по контрагенту, детализации продаж.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Дата начала периода (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Дата окончания периода (YYYY-MM-DD)"},
                    "counterparty": {"type": "string", "description": "Фильтр по контрагенту (подстрока)"},
                    "sum_min": {"type": "number", "description": "Минимальная сумма"},
                    "sum_max": {"type": "number", "description": "Максимальная сумма"},
                    "page": {"type": "integer", "description": "Номер страницы"},
                    "page_size": {"type": "integer", "description": "Размер страницы"},
                },
                "required": ["date_from", "date_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytics_context",
            "description": "Получить полный контекст для аналитики одним batch-запросом: итоги (сумма, кол-во заказов, средний чек), топ-20 товаров, топ-10 клиентов, остатки, неликвиды. Используй ВМЕСТО последовательных вызовов get_sales + get_sales_by_manager + get_stock, если нужна общая аналитика за период.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string",
                        "description": "Начальная дата в формате ISO (YYYY-MM-DD)",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Конечная дата в формате ISO (YYYY-MM-DD)",
                    },
                },
                "required": ["date_from", "date_to"],
            },
        },
    },
]

TOOL_NAME_TO_FUNC: dict[str, Any] = {}


def _import_tools() -> None:
    from src.tools import (
        abc_xyz_analysis_tool,
        compare_forecasts_tool,
        config_tool,
        create_chart_tool,
        describe_tool,
        forecast_sales_tool,
        forecast_stockout_tool,
        get_analytics_context_tool,
        get_purchases_tool,
        get_receivables_tool,
        get_sales_by_manager_tool,
        get_sales_documents_tool,
        get_sales_tool,
        get_stock_tool,
        get_structure_tool,
        list_nomenclature_tool,
        simulate_scenario_tool,
    )

    TOOL_NAME_TO_FUNC["get_stock"] = get_stock_tool
    TOOL_NAME_TO_FUNC["get_sales"] = get_sales_tool
    TOOL_NAME_TO_FUNC["get_sales_by_manager"] = get_sales_by_manager_tool
    TOOL_NAME_TO_FUNC["get_receivables"] = get_receivables_tool
    TOOL_NAME_TO_FUNC["get_purchases"] = get_purchases_tool
    TOOL_NAME_TO_FUNC["list_nomenclature"] = list_nomenclature_tool
    TOOL_NAME_TO_FUNC["create_chart"] = create_chart_tool
    TOOL_NAME_TO_FUNC["simulate_scenario"] = simulate_scenario_tool
    TOOL_NAME_TO_FUNC["abc_xyz_analysis"] = abc_xyz_analysis_tool
    TOOL_NAME_TO_FUNC["get_analytics_context"] = get_analytics_context_tool
    TOOL_NAME_TO_FUNC["get_sales_documents"] = get_sales_documents_tool
    TOOL_NAME_TO_FUNC["config"] = config_tool
    TOOL_NAME_TO_FUNC["describe"] = describe_tool
    TOOL_NAME_TO_FUNC["get_structure"] = get_structure_tool
    TOOL_NAME_TO_FUNC["forecast_sales"] = forecast_sales_tool
    TOOL_NAME_TO_FUNC["forecast_stockout"] = forecast_stockout_tool
    TOOL_NAME_TO_FUNC["compare_forecasts"] = compare_forecasts_tool


_import_tools()


class DeepSeekClient:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
            http_client=httpx.AsyncClient(timeout=120.0),
        )
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _call_llm(
        self,
        messages: list[ChatCompletionMessageParam],
        tools: list[ChatCompletionToolParam] | None = None,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        return response

    async def _run_conversation_loop(self, messages: list[ChatCompletionMessageParam]) -> dict[str, Any]:
        all_tool_calls: list[dict[str, Any]] = []
        total_input_tokens = 0
        total_output_tokens = 0

        for iteration in range(10):
            logger.debug("Итерация LLM #{}, сообщений: {}", iteration + 1, len(messages))
            response = await self._call_llm(messages, tools=TOOL_DEFINITIONS)
            choice = response.choices[0]

            total_input_tokens += response.usage.prompt_tokens if response.usage else 0
            total_output_tokens += response.usage.completion_tokens if response.usage else 0

            if choice.finish_reason == "stop":
                final_answer = choice.message.content or ""
                logger.info("LLM завершила с final ответом")
                return {"answer": final_answer, "tool_calls": all_tool_calls, "usage": {"prompt_tokens": total_input_tokens, "completion_tokens": total_output_tokens}}

            if choice.finish_reason == "tool_calls":
                msg = choice.message
                messages.append(msg)

                for tc in msg.tool_calls or []:
                    func_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    logger.info("LLM вызывает tool: {} с args={}", func_name, args)
                    func = TOOL_NAME_TO_FUNC.get(func_name)
                    if func is None:
                        result_text = f"Ошибка: неизвестный инструмент {func_name}"
                        result = None
                    else:
                        try:
                            result = await func(**args)
                            result_text = json.dumps(result, ensure_ascii=False, default=str)
                        except Exception as e:
                            result_text = f"Ошибка при вызове {func_name}: {e!s}"
                            result = None
                            logger.error("Ошибка tool {}: {}", func_name, e)

                    tool_entry: dict[str, Any] = {"name": func_name, "args": args}
                    if func_name == "create_chart" and result and "image_base64" in result:
                        tool_entry["result"] = {"chart_id": result.get("chart_id"), "image_base64": result["image_base64"], "image_url": result.get("image_url"), "chart_type": result.get("metadata", {}).get("chart_type")}
                    all_tool_calls.append(tool_entry)

                    logger.debug("Результат tool {}: {}", func_name, result_text[:200])
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_text})
                continue

            if choice.finish_reason == "length":
                final_answer = msg.content if (msg := choice.message).content else ""
                return {"answer": final_answer + "\n\n[Ответ обрезан из-за ограничения длины]", "tool_calls": all_tool_calls, "usage": {"prompt_tokens": total_input_tokens, "completion_tokens": total_output_tokens}}

        return {"answer": "Превышено максимальное количество итераций. Попробуйте уточнить запрос.", "tool_calls": all_tool_calls, "usage": {"prompt_tokens": total_input_tokens, "completion_tokens": total_output_tokens}}

    async def process_query(self, user_query: str) -> dict[str, Any]:
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]
        return await self._run_conversation_loop(messages)

    async def process_query_with_messages(self, messages: list[ChatCompletionMessageParam]) -> dict[str, Any]:
        return await self._run_conversation_loop(messages)

    async def ping(self) -> bool:
        try:
            response = await self._call_llm(
                messages=[{"role": "user", "content": "test"}],
            )
            return response.choices[0].finish_reason is not None
        except Exception:
            return False
