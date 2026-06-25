from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.chat.repository import ChatBase, ChatRepository

TEST_DB_URL = "sqlite+aiosqlite://"


@pytest.fixture
async def repo():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(ChatBase.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield ChatRepository(session)


class TestSessionCRUD:
    async def test_create(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        assert s.id and s.title == "Test" and s.user_id == "u"

    async def test_get(self, repo):
        s = await repo.create_session(user_id="u", title="Get Me")
        got = await repo.get_session(s.id)
        assert got and got.title == "Get Me"

    async def test_get_not_found(self, repo):
        assert await repo.get_session("nonexistent") is None

    async def test_list_sessions(self, repo):
        await repo.create_session(user_id="u1", title="S1")
        await repo.create_session(user_id="u1", title="S2")
        await repo.create_session(user_id="u2", title="S3")
        sessions = await repo.list_sessions(user_id="u1")
        assert len(sessions) == 2

    async def test_list_sessions_empty(self, repo):
        assert await repo.list_sessions(user_id="nobody") == []

    async def test_update_title(self, repo):
        s = await repo.create_session(user_id="u", title="Old")
        ok = await repo.update_session(s.id, title="New")
        assert ok
        got = await repo.get_session(s.id)
        assert got and got.title == "New"

    async def test_update_nonexistent(self, repo):
        ok = await repo.update_session("nope", title="X")
        assert not ok

    async def test_delete(self, repo):
        s = await repo.create_session(user_id="u", title="Del")
        ok = await repo.delete_session(s.id)
        assert ok
        assert await repo.get_session(s.id) is None

    async def test_delete_nonexistent(self, repo):
        assert not await repo.delete_session("nope")

    async def test_auto_title_from_first_message(self, repo):
        s = await repo.create_session(user_id="u", title="New")
        await repo.add_message(session_id=s.id, role="user", content="A" * 100)
        got = await repo.get_session(s.id)
        assert got and len(got.title) <= 53


class TestMessageCRUD:
    async def test_add_user_message(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        msg = await repo.add_message(session_id=s.id, role="user", content="Hello")
        assert msg.id and msg.role == "user" and msg.content == "Hello"

    async def test_add_assistant_message(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        msg = await repo.add_message(session_id=s.id, role="assistant", content="Hi!", tokens_used=50, response_time_ms=100)
        assert msg.tokens_used == 50
        assert msg.response_time_ms == 100

    async def test_get_messages_with_limit(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        for i in range(5):
            await repo.add_message(session_id=s.id, role="user", content=f"Msg {i}")
        msgs, total = await repo.get_messages(session_id=s.id, page=1, limit=3)
        assert len(msgs) == 3
        assert total == 5

    async def test_get_messages_empty(self, repo):
        msgs, total = await repo.get_messages(session_id="nope", page=1)
        assert msgs == []
        assert total == 0

    async def test_get_messages_second_page(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        for i in range(10):
            await repo.add_message(session_id=s.id, role="user", content=f"Msg {i}")
        msgs, total = await repo.get_messages(session_id=s.id, page=2, limit=3)
        assert len(msgs) == 3
        assert msgs[0].content == "Msg 3"
        assert total == 10

    async def test_context_messages(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        for i in range(10):
            await repo.add_message(session_id=s.id, role="user" if i % 2 == 0 else "assistant", content=f"M{i}", tokens_used=10)
        ctx = await repo.get_context_messages(session_id=s.id, max_tokens=30)
        assert 1 <= len(ctx) <= 4

    async def test_delete_message(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        msg = await repo.add_message(session_id=s.id, role="user", content="Hello")
        ok = await repo.delete_message(msg.id)
        assert ok
        msgs, _ = await repo.get_messages(session_id=s.id)
        assert len(msgs) == 0


class TestToolCalls:
    async def test_add_tool_call(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        msg = await repo.add_message(session_id=s.id, role="assistant", content="Result")
        tc = await repo.add_tool_call(message_id=msg.id, tool_name="get_stock", arguments={"item": "test"}, result='{"qty":10}', execution_time_ms=50, status="success")
        assert tc.id and tc.tool_name == "get_stock"

    async def test_get_tool_calls(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        msg = await repo.add_message(session_id=s.id, role="assistant", content="Result")
        await repo.add_tool_call(message_id=msg.id, tool_name="get_stock")
        calls = await repo.get_tool_calls(msg.id)
        assert len(calls) == 1
        assert calls[0]["tool_name"] == "get_stock"

    async def test_get_tool_calls_empty(self, repo):
        assert await repo.get_tool_calls("nope") == []


class TestSearch:
    async def test_search_by_session(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        await repo.add_message(session_id=s.id, role="user", content="продажи за январь")
        await repo.add_message(session_id=s.id, role="assistant", content="продажи составили 1 млн")
        results = await repo.search_messages(user_id="u", query="январь", session_id=s.id)
        assert len(results) >= 1
        assert "январь" in results[0]["content"]

    async def test_global_search(self, repo):
        s1 = await repo.create_session(user_id="u", title="S1")
        s2 = await repo.create_session(user_id="u", title="S2")
        await repo.add_message(session_id=s1.id, role="user", content="сколько товаров на складе")
        await repo.add_message(session_id=s2.id, role="user", content="продажи за март")
        results = await repo.search_messages(user_id="u", query="продажи")
        assert len(results) >= 1

    async def test_search_no_results(self, repo):
        results = await repo.search_messages(user_id="u", query="nonexistent12345")
        assert results == []


class TestCascade:
    async def test_delete_session_cascades_messages(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        await repo.add_message(session_id=s.id, role="user", content="M1")
        await repo.delete_session(s.id)
        msgs, _ = await repo.get_messages(session_id=s.id)
        assert len(msgs) == 0

    async def test_delete_message_cascades_tool_calls(self, repo):
        s = await repo.create_session(user_id="u", title="Test")
        msg = await repo.add_message(session_id=s.id, role="assistant", content="R")
        await repo.add_tool_call(message_id=msg.id, tool_name="t")
        await repo.delete_message(msg.id)
        calls = await repo.get_tool_calls(msg.id)
        assert calls == []
