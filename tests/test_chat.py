from __future__ import annotations

import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.chat.models import ChatMessage, ChatSession, ToolCall
from src.chat.repository import ChatBase, ChatRepository, ChatSessionDB
from src.chat.service import ChatService

TEST_DB_URL = "sqlite+aiosqlite://"


@pytest.fixture
async def db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(ChatBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_create_session(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="test_user", title="Test Chat")
    assert s.id
    assert s.title == "Test Chat"
    assert s.user_id == "test_user"


@pytest.mark.asyncio
async def test_list_sessions(db):
    repo = ChatRepository(db)
    await repo.create_session(user_id="u1", title="S1")
    await repo.create_session(user_id="u1", title="S2")
    await repo.create_session(user_id="u2", title="S3")
    sessions = await repo.list_sessions(user_id="u1")
    assert len(sessions) == 2


@pytest.mark.asyncio
async def test_add_message(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="u", title="Test")
    msg = await repo.add_message(session_id=s.id, role="user", content="Hello")
    assert msg.id
    assert msg.role == "user"
    assert msg.content == "Hello"


@pytest.mark.asyncio
async def test_add_assistant_message(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="u", title="Test")
    msg = await repo.add_message(session_id=s.id, role="assistant", content="Hi there!", tokens_used=50, response_time_ms=100)
    assert msg.tokens_used == 50
    assert msg.response_time_ms == 100


@pytest.mark.asyncio
async def test_get_messages_with_pagination(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="u", title="Test")
    for i in range(5):
        await repo.add_message(session_id=s.id, role="user", content=f"Msg {i}")
    msgs, total = await repo.get_messages(session_id=s.id, page=1, limit=3)
    assert len(msgs) == 3
    assert total == 5


@pytest.mark.asyncio
async def test_context_messages(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="u", title="Test")
    for i in range(10):
        await repo.add_message(session_id=s.id, role="user" if i % 2 == 0 else "assistant", content=f"Message {i}", tokens_used=10)
    ctx = await repo.get_context_messages(session_id=s.id, max_tokens=50)
    assert len(ctx) > 0
    assert all("role" in m and "content" in m for m in ctx)


@pytest.mark.asyncio
async def test_tool_call(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="u", title="Test")
    msg = await repo.add_message(session_id=s.id, role="assistant", content="Result")
    tc = await repo.add_tool_call(message_id=msg.id, tool_name="get_stock", arguments={"item": "test"}, result='{"qty": 10}', execution_time_ms=50, status="success")
    assert tc.id
    calls = await repo.get_tool_calls(msg.id)
    assert len(calls) == 1
    assert calls[0]["tool_name"] == "get_stock"


@pytest.mark.asyncio
async def test_search_messages(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="u", title="Test")
    await repo.add_message(session_id=s.id, role="user", content="сколько продаж за январь")
    await repo.add_message(session_id=s.id, role="assistant", content="продажи за январь составили 1 млн")
    results = await repo.search_messages(user_id="u", query="январь")
    assert len(results) >= 1
    assert "январь" in results[0]["content"]


@pytest.mark.asyncio
async def test_delete_session_cascades(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="u", title="Test")
    await repo.add_message(session_id=s.id, role="user", content="M1")
    await repo.delete_session(s.id)
    msgs, _ = await repo.get_messages(session_id=s.id)
    assert len(msgs) == 0


@pytest.mark.asyncio
async def test_auto_title_from_first_message(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="u", title="New Chat")
    long_text = "A" * 100
    await repo.add_message(session_id=s.id, role="user", content=long_text)
    updated = await repo.get_session(s.id)
    assert updated
    assert len(updated.title) <= 53  # 50 + "..."


@pytest.mark.asyncio
async def test_update_session_title(db):
    repo = ChatRepository(db)
    s = await repo.create_session(user_id="u", title="Old")
    await repo.update_session(s.id, title="New Title")
    updated = await repo.get_session(s.id)
    assert updated and updated.title == "New Title"


class TestChatService:
    @pytest.mark.asyncio
    async def test_process_message_handles_error(self, db):
        svc = ChatService(db)
        result = await svc.process_message(session_id="test-session", user_id="test", content="hello")
        assert "answer" in result

    @pytest.mark.asyncio
    async def test_process_message_creates_session(self, db):
        svc = ChatService(db)
        result = await svc.process_message(session_id="new-session-2", user_id="test", content="hello")
        assert "answer" in result

    @pytest.mark.asyncio
    async def test_error_handling(self, db):
        svc = ChatService(db)
        result = await svc.process_message(session_id="error-test", user_id="test", content="")
        assert "answer" in result
