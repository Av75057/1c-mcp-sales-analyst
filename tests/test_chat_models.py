from __future__ import annotations

from datetime import datetime

from src.chat.models import ChatMessage, ChatSession, ToolCall


class TestChatSession:
    def test_default_title(self):
        s = ChatSession(id="1", user_id="u")
        assert s.title == "Новый чат"
        assert s.is_archived is False
        assert s.messages_count == 0

    def test_is_archived_coerces_none(self):
        s = ChatSession.model_validate({"id": "1", "user_id": "u", "is_archived": None})
        assert s.is_archived is False

    def test_is_archived_coerces_int(self):
        s = ChatSession.model_validate({"id": "1", "user_id": "u", "is_archived": 1})
        assert s.is_archived is True
        s0 = ChatSession.model_validate({"id": "2", "user_id": "u", "is_archived": 0})
        assert s0.is_archived is False

    def test_auto_timestamps(self):
        s = ChatSession(id="1", user_id="u")
        assert isinstance(s.created_at, datetime)
        assert isinstance(s.updated_at, datetime)

    def test_title_custom(self):
        s = ChatSession(id="1", user_id="u", title="Test")
        assert s.title == "Test"


class TestChatMessage:
    def test_defaults(self):
        m = ChatMessage(id="m1", session_id="s1", role="user", content="Hello")
        assert m.tokens_used is None
        assert m.response_time_ms is None

    def test_assistant_message(self):
        m = ChatMessage(id="m1", session_id="s1", role="assistant", content="Hi", tokens_used=50, response_time_ms=100)
        assert m.tokens_used == 50
        assert m.response_time_ms == 100

    def test_role_validation(self):
        m = ChatMessage(id="m1", session_id="s1", role="user", content="test")
        assert m.role == "user"

    def test_auto_timestamp(self):
        m = ChatMessage(id="m1", session_id="s1", role="user", content="test")
        assert isinstance(m.created_at, datetime)


class TestToolCall:
    def test_defaults(self):
        tc = ToolCall(id="tc1", message_id="m1", tool_name="get_stock")
        assert tc.status == "success"
        assert tc.arguments is None

    def test_with_arguments(self):
        tc = ToolCall(id="tc1", message_id="m1", tool_name="get_stock", arguments={"item": "test"})
        assert tc.arguments == {"item": "test"}

    def test_error_status(self):
        tc = ToolCall(id="tc1", message_id="m1", tool_name="get_stock", status="error", error_message="Not found")
        assert tc.status == "error"
        assert tc.error_message == "Not found"

    def test_execution_time(self):
        tc = ToolCall(id="tc1", message_id="m1", tool_name="get_stock", execution_time_ms=150)
        assert tc.execution_time_ms == 150
