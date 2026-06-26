from __future__ import annotations

import json
from typing import Any

from src.logger import logger

CRITIC_PROMPT = """Ты — критик ответов AI-аналитика. Проверь ответ по критериям:
1. **Фактическая точность**: Все ли числа обоснованы данными?
2. **Полнота**: Ответил ли AI на все части вопроса?
3. **Логичность**: Нет ли логических ошибок?
4. **Конкретность**: Есть ли конкретные рекомендации?
5. **Ясность**: Понятен ли ответ?

Верни ТОЛЬКО JSON:
{"is_valid": true/false, "score": 0.0-1.0, "issues": [{"type": "hallucination|incomplete|illogical|missing_data", "severity": "critical|major|minor", "description": "...", "suggestion": "..."}], "reasoning": "..."}

Будь строгим. Если есть критические проблемы - is_valid: false."""


async def critique_response(user_query: str, ai_response: str, temperature: float = 0.3) -> dict[str, Any]:
    """Проверяет ответ AI через DeepSeek критика."""
    from src.deepseek_client import DeepSeekClient

    client = DeepSeekClient()
    try:
        response = await client._call_llm(
            messages=[
                {"role": "system", "content": CRITIC_PROMPT},
                {"role": "user", "content": f"Вопрос пользователя: {user_query}\n\nОтвет AI:\n{ai_response}\n\nПроверь ответ и верни JSON."},
            ],
            tools=None,
        )
        content = response.choices[0].message.content or ""
        # Extract JSON from response
        if "{" in content:
            json_str = content[content.index("{"): content.rindex("}") + 1]
            return json.loads(json_str)
        return {"is_valid": True, "score": 0.7, "issues": [], "reasoning": "Не удалось распарсить критику"}
    except Exception as e:
        logger.warning("[Reflection] Critique failed: {}", e)
        return {"is_valid": True, "score": 0.7, "issues": [], "reasoning": f"Ошибка критика: {e}"}


async def generate_with_reflection(user_query: str, ai_response: str, max_iterations: int = 2) -> tuple[str, dict[str, Any]]:
    """Генерирует ответ с самопроверкой."""
    current = ai_response
    metadata: dict[str, Any] = {"iterations": 0, "scores": [], "issues_found": 0}

    for iteration in range(max_iterations):
        critique = await critique_response(user_query, current)
        metadata["scores"].append(critique.get("score", 0.0))

        if critique.get("is_valid", False) and critique.get("score", 0.0) >= 0.7:
            break

        issues = critique.get("issues", [])
        if not issues:
            break

        metadata["issues_found"] += len(issues)
        logger.info("[Reflection] Iteration {}: {} issues found", iteration + 1, len(issues))

        # Improvement prompt
        from src.deepseek_client import DeepSeekClient, SYSTEM_PROMPT

        issues_text = "\n".join(f"- [{i['severity']}] {i['type']}: {i['description']}. Предложение: {i.get('suggestion', '')}" for i in issues)
        improvement_prompt = f"Твой предыдущий ответ был проверен критиком. Найдены проблемы:\n{issues_text}\n\nИсправь их в улучшенном ответе.\n\nОригинальный вопрос: {user_query}\nТвой предыдущий ответ: {current}"

        client = DeepSeekClient()
        try:
            resp = await client._call_llm(
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": improvement_prompt}],
            )
            current = resp.choices[0].message.content or current
            metadata["iterations"] += 1
        except Exception as e:
            logger.warning("[Reflection] Improvement failed: {}", e)
            break

    return current, metadata
