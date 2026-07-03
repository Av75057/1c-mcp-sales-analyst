from __future__ import annotations

import json
from datetime import date
from typing import Any

from src.dashboard.guardrails import validate_chart_config, GuardrailError
from src.dashboard.schemas import ChartConfig
from src.deepseek_client import DeepSeekClient
from src.logger import logger

SYSTEM_PROMPT = """Ты — AI-аналитик для 1С:УНФ. Преобразуй запрос пользователя в JSON-конфигурацию графика.

## ТИПЫ ГРАФИКОВ:
- line → временные ряды, тренды, динамика (по дням/неделям/месяцам)
- bar → сравнение категорий, топ-N, рейтинги
- pie → структура, доли (максимум 7 категорий)

## ПЕРИОДЫ:
- не указан → last_30_days
- "на этой неделе" → last_7_days
- "в этом квартале" → last_quarter
- "в этом году" → last_year

## ДОПУСТИМЫЕ СУЩНОСТИ И ПОЛЯ:
Document.РеализацияТоваровУслуг: Дата, Контрагент, Номенклатура, Сумма, Количество, Менеджер
Document.ЗаказКлиента: Дата, Контрагент, Сумма, Статус, Менеджер
Catalog.Номенклатура: Наименование, Артикул, Группа, Цена
Register.Продажи: Период, Номенклатура, Контрагент, Сумма, Количество

## ЦВЕТА: #5470c6, #91cc75, #fac858, #ee6666, #73c0de

## ФОРМАТ ОТВЕТА (ТОЛЬКО JSON):
{"chart_type": "line|bar|pie", "title": "...", "x_axis": {"field": "...", "label": "...", "type": "time|category"}, "y_axis": {"field": "...", "label": "...", "type": "category"}, "series": [{"name": "...", "field": "...", "color": "#..."}], "group_by": ["..."], "order_by": {"field": "...", "direction": "desc"}, "limit": 50, "drill_down": {"enabled": false}, "onec_query": {"entity": "...", "fields": ["..."], "period": "last_30_days", "aggregation": "sum"}}

Текущая дата: {current_date}
Запрос пользователя: {user_query}"""


async def generate_chart_config(user_query: str, max_retries: int = 2) -> ChartConfig:
    client = DeepSeekClient()
    prompt = SYSTEM_PROMPT.format(current_date=date.today().isoformat(), user_query=user_query)

    for attempt in range(max_retries):
        try:
            response = await client._call_llm(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            content = response.choices[0].message.content or ""
            json_str = content[content.index("{"): content.rindex("}") + 1] if "{" in content and "}" in content else content
            config = json.loads(json_str)

            validate_chart_config(config)
            return ChartConfig(**config)

        except (json.JSONDecodeError, GuardrailError, Exception) as e:
            logger.warning("[Dashboard] LLM attempt {}/{} failed: {}", attempt + 1, max_retries, e)
            if attempt == max_retries - 1:
                raise ValueError(f"Не удалось сгенерировать график: {e}")
