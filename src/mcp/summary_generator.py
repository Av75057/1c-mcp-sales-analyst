from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Optional

from src.cache import cache
from src.config import settings
from src.deepseek_client import DeepSeekClient
from src.logger import logger

EXECUTIVE_SUMMARY_PROMPT = """
Ты — AI-аналитик для руководителя компании. Твоя задача — проанализировать KPI-данные
и составить краткую, содержательную сводку на русском языке.

## ВХОДНЫЕ ДАННЫЕ:
{kpi_data_json}

Период: {period_label}
Организация: {organization}

## ТРЕБОВАНИЯ К АНАЛИЗУ:

1. **Главный инсайт** (1 предложение):
   - Начни с самого важного достижения или проблемы
   - Используй конкретные цифры из данных

2. **Аномалии** (обязательно выдели, если есть):
   - Тренд > +20% или < -20% считается аномалией
   - Для каждой аномалии укажи: что произошло, насколько, возможную причину
   - Используй эмодзи: 📈 для роста, 📉 для падения, ⚠️ для критичных отклонений

3. **Рекомендации** (1-2 конкретных действия):
   - Должны быть практичными и выполнимыми
   - Ссылайся на конкретные данные из сводки

4. **Контекстные сравнения** (если уместно):
   - Сравни с предыдущим периодом
   - Упомяни сезонность, если виден паттерн

## ФОРМАТ ОТВЕТА (Markdown):

💡 **Главное:** [1 предложение с ключевым выводом]

📊 **Ключевые показатели:**
- [Показатель 1]: [значение] ([тренд])
- [Показатель 2]: [значение] ([тренд])

⚠️ **Внимание (аномалии):**
- [Аномалия 1 с объяснением]
- [Аномалия 2 с объяснением]

🎯 **Рекомендации:**
1. [Конкретное действие 1]
2. [Конкретное действие 2]

## ОГРАНИЧЕНИЯ:
- Максимум 200 слов
- Используй только данные из входного JSON (не выдумывай)
- Если данных недостаточно — честно скажи об этом
- Тон: деловой, но не сухой
"""


async def generate_executive_summary(
    period: str,
    kpi_data: dict,
    organization: Optional[str] = None,
) -> dict:
    kpi_hash = hashlib.md5(json.dumps(kpi_data, sort_keys=True).encode()).hexdigest()[:12]
    today_str = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"summary:{period}:{organization or 'all'}:{today_str}:{kpi_hash}"

    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("[Summary] Cache HIT: {}", cache_key)
        return {**cached, "cache_status": "hit"}

    logger.info("[Summary] Cache MISS. Generating via DeepSeek: {}", cache_key)

    period_labels = {
        "today": "Сегодня", "yesterday": "Вчера",
        "this_week": "Эта неделя", "last_week": "Прошлая неделя",
        "this_month": "Этот месяц", "last_month": "Прошлый месяц",
        "this_quarter": "Этот квартал", "this_year": "Этот год",
    }

    prompt = EXECUTIVE_SUMMARY_PROMPT.format(
        kpi_data_json=json.dumps(kpi_data, ensure_ascii=False, indent=2),
        period_label=period_labels.get(period, period),
        organization=organization or "Все организации",
    )

    try:
        ds = DeepSeekClient()
        response = await ds._call_llm(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7,
        )

        choice = response.choices[0]
        text = choice.message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0
        finish_reason = choice.finish_reason if hasattr(choice, 'finish_reason') else 'unknown'
        logger.info("[Summary] DeepSeek finish_reason={}, tokens={}", finish_reason, tokens_used)

        parsed = _parse_response(text)
        result = {
            **parsed,
            "generated_at": datetime.utcnow().isoformat(),
            "tokens_used": tokens_used,
            "cache_status": "miss",
        }

        cache.set(cache_key, result, ttl=1800)
        return result

    except Exception as e:
        logger.warning("[Summary] DeepSeek failed, using fallback: {}", e)
        return _generate_fallback(kpi_data, period)


def _parse_response(text: str) -> dict:
    key_insights = []
    recommendations = []
    anomalies = []
    current_section = None

    for line in text.split("\n"):
        line = line.strip()
        if "💡" in line or "Главное" in line:
            key_insights.append(line)
        elif "⚠️" in line or "Внимание" in line:
            current_section = "anomalies"
        elif "🎯" in line or "Рекомендации" in line:
            current_section = "recommendations"
        elif current_section == "anomalies" and line.startswith("-"):
            anomalies.append(line.lstrip("- ").strip())
        elif current_section == "recommendations" and (line.startswith("1.") or line.startswith("2.")):
            recommendations.append(line[2:].strip().lstrip(". ").strip())

    return {
        "summary_text": text,
        "key_insights": key_insights[:3],
        "recommendations": recommendations[:2],
        "anomalies": anomalies[:3],
    }


def _generate_fallback(kpi_data: dict, period: str) -> dict:
    revenue = kpi_data.get("revenue", {}).get("current", 0)
    trend = kpi_data.get("revenue", {}).get("trend_percent", 0)
    profit = kpi_data.get("profit", {}).get("current", 0)
    orders = kpi_data.get("orders_count", {}).get("current", 0)
    margin = kpi_data.get("margin_percent", {}).get("current", 0)

    trend_arrow = "📈" if trend >= 0 else "📉"

    text = (
        f"💡 **Главное:** Выручка за период составила {revenue:,.0f} ₽ "
        f"({trend_arrow} {trend:+.1f}% к прошлому периоду).\n\n"
        f"📊 **Ключевые показатели:**\n"
        f"- Выручка: {revenue:,.0f} ₽ ({trend_arrow} {trend:+.1f}%)\n"
        f"- Прибыль: {profit:,.0f} ₽\n"
        f"- Заказы: {orders:.0f}\n"
        f"- Маржа: {margin:.1f}%\n\n"
        f"⚠️ **AI-анализ временно недоступен.**\n"
        f"Пожалуйста, ознакомьтесь с детализацией в графиках ниже."
    )

    return {
        "summary_text": text,
        "key_insights": [f"Выручка: {revenue:,.0f} ₽"],
        "recommendations": [],
        "anomalies": [],
        "generated_at": datetime.utcnow().isoformat(),
        "tokens_used": 0,
        "cache_status": "fallback",
    }
