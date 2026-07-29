#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import io
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from openpyxl import Workbook

from src.clients.c1_client import C1Client
from src.config import settings
from src.deepseek_client import DeepSeekClient
from src.logger import logger
from src.tools import get_client, close_client

st.set_page_config(
    page_title="1C MCP Sales Analyst",
    page_icon="📊",
    layout="wide",
)

PAGES = ["💬 Чат", "📦 Остатки", "💰 Продажи", "📊 Дашборд", "🤖 Инсайты"]


def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return output.getvalue()


def render_chat():
    st.title("💬 AI-аналитик")
    st.markdown("Задайте вопрос на русском языке про остатки, продажи или долги.")

    EXAMPLE_QUERIES = [
        "Покажи топ-10 товаров по остаткам",
        "Какая выручка за последние 30 дней?",
        "Сколько полотенец на остатке?",
        "Продажи по менеджерам за всё время",
        "Какие товары не продавались дольше всего?",
    ]

    for q in EXAMPLE_QUERIES:
        if st.button(f"📌 {q}", use_container_width=True, key=f"ex_{q[:20]}"):
            st.session_state.query = q

    query = st.text_input(
        "Введите запрос:",
        value=st.session_state.get("query", ""),
        placeholder="Например: топ-10 товаров по остаткам",
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
                            if tc["name"] == "create_chart" and "result" in tc:
                                from PIL import Image
                                import base64, io
                                img_bytes = base64.b64decode(tc["result"]["image_base64"])
                                st.image(Image.open(io.BytesIO(img_bytes)), use_container_width=True)

                usage = result["usage"]
                col1, col2, col3 = st.columns(3)
                col1.metric("Токенов на вход", usage["prompt_tokens"])
                col2.metric("Токенов на выход", usage["completion_tokens"])
                cost = (usage["prompt_tokens"] * 0.00000027 + usage["completion_tokens"] * 0.0011) / 1000000 * 100
                col3.metric("Стоимость", f"${cost:.6f}")

            except Exception as e:
                logger.error("Ошибка: {}", e)
                st.error(f"⚠️ Произошла ошибка: {e!s}")


def render_stock():
    st.title("📦 Остатки товаров")
    c1 = C1Client()

    col1, col2 = st.columns(2)
    with col1:
        search = st.text_input("🔍 Поиск по названию", placeholder="полотенце, гвоздь...")
    with col2:
        min_qty = st.number_input("Минимальное количество", min_value=0, value=0)

    if st.button("🔄 Загрузить", type="primary"):
        with st.spinner("Загружаю остатки..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(
                c1.get_stock(
                    nomenclature=search or None,
                    min_quantity=min_qty or None,
                )
            )
            loop.close()

        if not data:
            st.warning("Нет данных по заданным фильтрам")
            return

        df = pd.DataFrame(data)
        df.columns = ["Товар", "Организация", "Количество", "Ед."]

        # График топ-20
        st.subheader("🏆 Топ товаров по остаткам")
        top = df.nlargest(20, "Количество")
        fig = px.bar(
            top,
            x="Количество",
            y="Товар",
            orientation="h",
            title=f"Топ-{min(20, len(top))} товаров",
            text_auto=True,
        )
        fig.update_layout(height=500, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

        # Таблица
        st.subheader("📋 Полная таблица")
        st.dataframe(df, use_container_width=True, height=400)

        # Excel
        excel_data = to_excel(df)
        st.download_button(
            label="📥 Скачать Excel",
            data=excel_data,
            file_name=f"остатки_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_sales():
    st.title("💰 Продажи")
    c1 = C1Client()

    col1, col2, col3 = st.columns(3)
    with col1:
        date_from = st.date_input("Дата с", value=date.today() - timedelta(days=30))
    with col2:
        date_to = st.date_input("Дата по", value=date.today())
    with col3:
        manager = st.text_input("Менеджер", placeholder="Кузнецов, Киреева...")

    if st.button("🔄 Загрузить", type="primary"):
        with st.spinner("Загружаю продажи..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(
                c1.get_sales(
                    date_from=date_from.isoformat(),
                    date_to=date_to.isoformat(),
                    manager=manager or None,
                )
            )
            # sales by manager
            by_manager = loop.run_until_complete(
                c1.get_sales_by_manager(
                    date_from=date_from.isoformat(),
                    date_to=date_to.isoformat(),
                )
            )
            loop.close()

        if not data:
            st.warning("Нет данных по заданным фильтрам")
            return

        df = pd.DataFrame(data)
        mapped = {
            "date": "Дата", "nomenclature": "Товар", "quantity": "Количество",
            "sum": "Сумма", "manager": "Менеджер", "warehouse": "Организация",
        }
        df = df.rename(columns=mapped)
        df = df[list(mapped.values())]

        # Метрики
        total_sum = df["Сумма"].sum()
        total_qty = df["Количество"].sum()
        col1, col2 = st.columns(2)
        col1.metric("💰 Общая выручка", f"{total_sum:,.0f} ₽")
        col2.metric("📦 Всего единиц", f"{total_qty:,.0f}")

        # Продажи по дням
        st.subheader("📈 Продажи по дням")
        daily = df.groupby("Дата", as_index=False)["Сумма"].sum().sort_values("Дата")
        fig = px.line(daily, x="Дата", y="Сумма", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # По менеджерам
        if by_manager:
            st.subheader("👤 Продажи по менеджерам")
            df_mgr = pd.DataFrame(by_manager)
            df_mgr.columns = ["Менеджер", "Сумма", "Количество"]
            fig = px.pie(df_mgr, values="Сумма", names="Менеджер", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        # Таблица
        st.subheader("📋 Детализация")
        st.dataframe(df, use_container_width=True, height=400)

        excel_data = to_excel(df)
        st.download_button(
            label="📥 Скачать Excel",
            data=excel_data,
            file_name=f"продажи_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_dashboard():
    st.title("📊 Дашборд")
    c1 = C1Client()

    with st.spinner("Загружаю данные..."):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stock, sales, by_manager = loop.run_until_complete(
            asyncio.gather(
                c1.get_stock(),
                c1.get_sales(date_from=(date.today() - timedelta(days=30)).isoformat(), date_to=date.today().isoformat()),
                c1.get_sales_by_manager(),
            )
        )
        loop.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Позиций на остатке", len(stock))
    col2.metric("💰 Выручка за 30 дней", f"{sum(s['sum'] for s in sales):,.0f} ₽" if sales else "0 ₽")
    col3.metric("👤 Менеджеров", len(by_manager))

    st.subheader("🏆 Топ-10 товаров на складе")
    if stock:
        df = pd.DataFrame(stock)
        df.columns = ["Товар", "Организация", "Количество", "Ед."]
        top = df.nlargest(10, "Количество")
        fig = px.bar(top, x="Количество", y="Товар", orientation="h", text_auto=True)
        fig.update_layout(height=400, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top, use_container_width=True)

    st.subheader("👤 Продажи по менеджерам")
    if by_manager:
        df_mgr = pd.DataFrame(by_manager)
        df_mgr.columns = ["Менеджер", "Сумма", "Количество"]
        fig = px.pie(df_mgr, values="Сумма", names="Менеджер", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)


def render_insights():
    st.title("🤖 AI Инсайты")

    from pathlib import Path
    import json
    from datetime import datetime

    sent_dir = Path(__file__).resolve().parent / "data" / "sent_insights"
    if not sent_dir.exists():
        st.info("Нет инсайтов. Запусти `python run_insights.py scan` чтобы сгенерировать.")
        return

    files = sorted(sent_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        st.info("Нет отправленных инсайтов")
        return

    st.markdown(f"Всего инсайтов: **{len(files)}**")

    for path in files:
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        sent_at = data.get("sent_at", "")[:16].replace("T", " ")
        priority = data.get("priority", "info")
        emoji = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}.get(priority, "ℹ️")
        title = data.get("title", data.get("detector", "unknown"))

        with st.container():
            cols = st.columns([1, 6, 2])
            cols[0].markdown(emoji)
            cols[1].markdown(f"**{title}**  \n{data.get('detector', '')} · {data.get('entity_id', '')}")
            cols[2].markdown(f"`{sent_at}`")


def main():
    with st.sidebar:
        st.image("https://cdn.jsdelivr.net/gh/opencode-ai/opencode@main/docs/public/logo.svg", width=40)
        st.title("1C Аналитик")
        st.markdown("---")
        page = st.radio("Раздел", PAGES, label_visibility="collapsed")
        st.markdown("---")
        st.caption("1C:УНФ + MCP + DeepSeek")
        st.caption(f"Данные: {'реальные 1С' if not settings.use_mock_data else 'мок'}")

    if page == PAGES[0]:
        render_chat()
    elif page == PAGES[1]:
        render_stock()
    elif page == PAGES[2]:
        render_sales()
    elif page == PAGES[3]:
        render_dashboard()
    elif page == PAGES[4]:
        render_insights()


if __name__ == "__main__":
    main()
