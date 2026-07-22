from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

from src.chat.models import ChatMessage, ChatSession, ToolCall

ChatBase = declarative_base()


class ChatSessionDB(ChatBase):
    __tablename__ = "chat_sessions"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=False, default="Новый чат")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_archived = Column(Integer, default=0)


class ChatMessageDB(ChatBase):
    __tablename__ = "chat_messages"
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ToolCallDB(ChatBase):
    __tablename__ = "tool_calls"
    id = Column(String(36), primary_key=True)
    message_id = Column(String(36), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    arguments = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def init_db(self) -> None:
        async with self.db.bind.begin() as conn:
            await conn.run_sync(ChatBase.metadata.create_all)

    # === Session CRUD ===

    async def create_session(self, user_id: str, title: str = "Новый чат") -> ChatSession:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        await self.db.execute(
            text("INSERT INTO chat_sessions (id, user_id, title, is_archived, created_at, updated_at) VALUES (:id, :uid, :title, 0, :now, :now)"),
            {"id": session_id, "uid": user_id, "title": title, "now": now},
        )
        await self.db.commit()
        return ChatSession(id=session_id, user_id=user_id, title=title)

    async def get_session(self, session_id: str) -> ChatSession | None:
        row = await self.db.execute(text("SELECT * FROM chat_sessions WHERE id = :id"), {"id": session_id})
        r = dict(row.mappings().first() or {})
        if not r:
            return None
        if r.get("is_archived") is None:
            r["is_archived"] = False
        return ChatSession(**r)

    async def list_sessions(self, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = await self.db.execute(
            text("SELECT * FROM chat_sessions WHERE user_id = :uid AND is_archived = 0 ORDER BY updated_at DESC LIMIT :lim"),
            {"uid": user_id, "lim": limit},
        )
        result = []
        for r in rows.mappings().all():
            d = dict(r)
            if d.get("is_archived") is None:
                d["is_archived"] = False
            # Get message count
            cnt_row = await self.db.execute(text("SELECT COUNT(*) as cnt FROM chat_messages WHERE session_id = :sid"), {"sid": d["id"]})
            cnt = cnt_row.mappings().first()["cnt"]
            # Get last message preview
            last_row = await self.db.execute(text("SELECT content FROM chat_messages WHERE session_id = :sid ORDER BY created_at DESC LIMIT 1"), {"sid": d["id"]})
            last = last_row.mappings().first()
            last_msg = last["content"][:80] if last else ""

            result.append({
                "id": d["id"],
                "title": d["title"],
                "created_at": d["created_at"].isoformat() if hasattr(d["created_at"], "isoformat") else str(d["created_at"]),
                "updated_at": d["updated_at"].isoformat() if hasattr(d["updated_at"], "isoformat") else str(d["updated_at"]),
                "messages_count": cnt,
                "last_message_preview": last_msg,
            })
        return result

    async def update_session(self, session_id: str, **kwargs: Any) -> bool:
        sets = ", ".join(f"{k} = :{k}" for k in kwargs)
        params = {**kwargs, "id": session_id}
        params["now"] = datetime.utcnow()
        r = await self.db.execute(
            text(f"UPDATE chat_sessions SET {sets}, updated_at = :now WHERE id = :id"),
            params,
        )
        await self.db.commit()
        return r.rowcount > 0

    async def delete_session(self, session_id: str) -> bool:
        await self.db.execute(text("DELETE FROM tool_calls WHERE message_id IN (SELECT id FROM chat_messages WHERE session_id = :sid)"), {"sid": session_id})
        await self.db.execute(text("DELETE FROM chat_messages WHERE session_id = :sid"), {"sid": session_id})
        r = await self.db.execute(text("DELETE FROM chat_sessions WHERE id = :id"), {"id": session_id})
        await self.db.commit()
        return r.rowcount > 0

    # === Message CRUD ===

    async def add_message(self, session_id: str, role: str, content: str, tokens_used: int | None = None, response_time_ms: int | None = None) -> ChatMessage:
        msg_id = str(uuid.uuid4())
        now = datetime.utcnow()
        await self.db.execute(
            text("INSERT INTO chat_messages (id, session_id, role, content, tokens_used, response_time_ms, created_at) VALUES (:id, :sid, :role, :content, :tokens, :rtime, :now)"),
            {"id": msg_id, "sid": session_id, "role": role, "content": content, "tokens": tokens_used, "rtime": response_time_ms, "now": now},
        )
        # Update session's updated_at and title from first user message
        await self.db.execute(text("UPDATE chat_sessions SET updated_at = :now WHERE id = :sid"), {"now": now, "sid": session_id})
        if role == "user":
            # Auto-title from first user message
            row = await self.db.execute(text("SELECT COUNT(*) as cnt FROM chat_messages WHERE session_id = :sid"), {"sid": session_id})
            cnt = row.mappings().first()["cnt"]
            if cnt == 1:
                title = content[:50] + ("..." if len(content) > 50 else "")
                await self.db.execute(text("UPDATE chat_sessions SET title = :title WHERE id = :sid"), {"title": title, "sid": session_id})
        await self.db.commit()
        return ChatMessage(id=msg_id, session_id=session_id, role=role, content=content, tokens_used=tokens_used, response_time_ms=response_time_ms)

    async def get_messages(self, session_id: str, page: int = 1, limit: int = 50) -> tuple[list[ChatMessage], int]:
        offset = (page - 1) * limit
        row = await self.db.execute(text("SELECT COUNT(*) as cnt FROM chat_messages WHERE session_id = :sid"), {"sid": session_id})
        total = row.mappings().first()["cnt"]
        rows = await self.db.execute(
            text("SELECT * FROM chat_messages WHERE session_id = :sid ORDER BY created_at ASC LIMIT :lim OFFSET :off"),
            {"sid": session_id, "lim": limit, "off": offset},
        )
        messages = [ChatMessage(**r) for r in rows.mappings().all()]
        return messages, total

    async def get_context_messages(self, session_id: str, max_tokens: int = 3000) -> list[dict[str, str]]:
        rows = await self.db.execute(
            text("SELECT role, content, tokens_used FROM chat_messages WHERE session_id = :sid ORDER BY created_at DESC"),
            {"sid": session_id},
        )
        messages = [{"role": r["role"], "content": r["content"], "tokens": r["tokens_used"] or len(r["content"]) // 4} for r in rows.mappings().all()]

        context = []
        total = 0
        for msg in reversed(messages):
            tokens = msg["tokens"]
            if total + tokens > max_tokens:
                break
            context.append({"role": msg["role"], "content": msg["content"]})
            total += tokens
        return context

    async def delete_message(self, message_id: str) -> bool:
        await self.db.execute(text("DELETE FROM tool_calls WHERE message_id = :mid"), {"mid": message_id})
        r = await self.db.execute(text("DELETE FROM chat_messages WHERE id = :id"), {"id": message_id})
        await self.db.commit()
        return r.rowcount > 0

    # === Tool Calls ===

    async def add_tool_call(self, message_id: str, tool_name: str, arguments: dict | None = None, result: str | None = None, execution_time_ms: int | None = None, status: str = "success", error_message: str | None = None) -> ToolCall:
        call_id = str(uuid.uuid4())
        await self.db.execute(
            text("INSERT INTO tool_calls (id, message_id, tool_name, arguments, result, execution_time_ms, status, error_message) VALUES (:id, :mid, :name, :args, :res, :time, :status, :err)"),
            {"id": call_id, "mid": message_id, "name": tool_name, "args": json.dumps(arguments) if arguments else None, "res": result[:10000] if result else None, "time": execution_time_ms, "status": status, "err": error_message},
        )
        await self.db.commit()
        return ToolCall(id=call_id, message_id=message_id, tool_name=tool_name, arguments=arguments, result=result, execution_time_ms=execution_time_ms, status=status, error_message=error_message)

    async def get_tool_calls(self, message_id: str) -> list[dict[str, Any]]:
        rows = await self.db.execute(
            text("SELECT id, tool_name, arguments, result, execution_time_ms, status, error_message FROM tool_calls WHERE message_id = :mid ORDER BY created_at ASC"),
            {"mid": message_id},
        )
        return [dict(r) for r in rows.mappings().all()]

    async def search_messages(self, user_id: str, query: str, session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        like = f"%{query}%"
        if session_id:
            rows = await self.db.execute(
                text("SELECT cm.*, cs.title as session_title FROM chat_messages cm JOIN chat_sessions cs ON cm.session_id = cs.id WHERE cm.session_id = :sid AND cm.content LIKE :q AND cs.user_id = :uid ORDER BY cm.created_at DESC LIMIT :lim"),
                {"sid": session_id, "q": like, "uid": user_id, "lim": limit},
            )
        else:
            rows = await self.db.execute(
                text("SELECT cm.*, cs.title as session_title FROM chat_messages cm JOIN chat_sessions cs ON cm.session_id = cs.id WHERE cs.user_id = :uid AND cm.content LIKE :q ORDER BY cm.created_at DESC LIMIT :lim"),
                {"uid": user_id, "q": like, "lim": limit},
            )
        return [dict(r) for r in rows.mappings().all()]
