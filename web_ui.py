#!/usr/bin/env python3
from __future__ import annotations

import asyncio

import streamlit as st

from src.config import settings
from src.deepseek_client import DeepSeekClient
from src.logger import logger

st.set_page_config(
    page_title="1C MCP Sales Analyst",
    page_icon="📊",
    layout="centered",
)

st.title("📊 1C + MCP + DeepSeek")
st.markdown("**AI-аналитик склада и продаж** — задайте вопрос на русском языке")

EXAMPLE_QUERIES = [
    "Покажи топ-5 товаров на складе в Москве, которые не продавались 30 дней",
    "Какая выручка за последнюю неделю по менеджеру Иванов?",
    "Сколько единиц товара 'Гвоздь 100мм' на всех складах?",
    "Кто из клиентов задолжал больше 100 000 рублей?",
    "Какие продажи были за последние 10 дней?",
]

if "history" not in st.session_state:
    st.session_state.history = []

for q in EXAMPLE_QUERIES:
    if st.button(f"📌 {q}", use_container_width=True):
        st.session_state.query = q

query = st.text_input(
    "Введите запрос:",
    value=st.session_state.get("query", ""),
    placeholder="Например: топ-5 непродающихся товаров в Москве",
)

if query:
    st.session_state.query = query

    try:
        settings.validate()
    except ValueError as e:
        st.error(f"⚠️ {e}")
        st.stop()

    with st.spinner("🤔 Анализирую данные..."):
        try:
            client = DeepSeekClient()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(client.process_query(query))
            loop.close()

            st.markdown("### 📋 Ответ")
            st.markdown(result["answer"])

            if result["tool_calls"]:
                with st.expander("🤖 Что вызывал AI"):
                    for tc in result["tool_calls"]:
                        args_str = ", ".join(f"{k}={v}" for k, v in tc["args"].items())
                        st.code(f"{tc['name']}({args_str})", language="text")

            usage = result["usage"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Токенов на вход", usage["prompt_tokens"])
            col2.metric("Токенов на выход", usage["completion_tokens"])
            cost = (usage["prompt_tokens"] * 0.00000027 + usage["completion_tokens"] * 0.0011) / 1000000 * 100
            col3.metric("Стоимость", f"${cost:.6f}")

        except Exception as e:
            logger.error("Ошибка: {}", e)
            st.error(f"⚠️ Произошла ошибка: {e!s}")
