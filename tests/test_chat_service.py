from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.chat.repository import ChatBase, ChatRepository
from src.chat.service import ChatService

TEST_DB_URL = "sqlite+aiosqlite://"


@pytest.fixture
async def repo():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(ChatBase.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield ChatRepository(session)


@pytest.fixture
async def svc(repo):
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(ChatBase.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield ChatService(session)


class TestChatService:
    async def test_process_message_creates_session(self, svc):
        result = await svc.process_message(session_id="new-session", user_id="admin", content="привет")
        assert "answer" in result
        assert result["session_id"] == "new-session"

    async def test_process_message_includes_usage(self, svc):
        result = await svc.process_message(session_id="usage-test", user_id="admin", content="скажи 'тест'")
        assert "usage" in result
        assert result["usage"]["completion_tokens"] >= 0

    async def test_process_message_saves_messages(self, svc):
        await svc.process_message(session_id="save-test", user_id="admin", content="hello")
        msgs, total = await svc.repo.get_messages(session_id="save-test")
        assert total >= 2

    async def test_process_message_handles_empty_content(self, svc):
        result = await svc.process_message(session_id="empty-test", user_id="admin", content="")
        assert "answer" in result

    async def test_context_is_limited(self, svc):
        for i in range(20):
            await svc.repo.add_message(session_id="ctx-test", role="user", content=f"long message number {i}" * 10, tokens_used=100)
        result = await svc.process_message(session_id="ctx-test", user_id="admin", content="final")
        assert "answer" in result
