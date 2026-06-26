from __future__ import annotations

import json
from datetime import datetime
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from src.chat.models import ChatMessage
from src.chat.repository import ChatRepository
from src.deepseek_client import DeepSeekClient
from src.guardrails.injection_detector import injection_detector
from src.guardrails.number_verifier import number_verifier
from src.logger import logger


class ChatService:
    def __init__(self, db: AsyncSession):
        self.repo = ChatRepository(db)
        self._deepseek = DeepSeekClient()

    async def process_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        max_context_tokens: int = 3000,
    ) -> dict[str, Any]:
        # 0. Check prompt injection
        if injection_detector.detect(content):
            return {"session_id": session_id, "answer": "⚠️ Обнаружена подозрительная активность. Запрос отклонён.", "tool_calls": [], "usage": {"prompt_tokens": 0, "completion_tokens": 0}}

        # 1. Check session exists, create if not
        session = await self.repo.get_session(session_id)
        if not session:
            session = await self.repo.create_session(user_id=user_id, title="Новый чат")

        # 2. Save user message
        user_msg = await self.repo.add_message(session_id=session_id, role="user", content=content)

        # 3. Get context history
        history = await self.repo.get_context_messages(session_id=session_id, max_tokens=max_context_tokens)

        # 4. Build messages for DeepSeek
        from src.deepseek_client import SYSTEM_PROMPT

        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history, {"role": "user", "content": content}]

        # 5. Call DeepSeek
        start = datetime.utcnow()
        try:
            result = await self._deepseek.process_query_with_messages(messages)
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000

            # 6. Save assistant message
            assistant_msg = await self.repo.add_message(
                session_id=session_id,
                role="assistant",
                content=result["answer"],
                tokens_used=result["usage"]["completion_tokens"],
                response_time_ms=int(elapsed),
            )

            # 7. Verify numbers with guardrails
            try:
                number_verifier.verify_and_log(result["answer"], result)
            except Exception:
                pass

            # 8. Save tool calls
            tool_calls_saved = []
            for tc in result.get("tool_calls", []):
                saved = await self.repo.add_tool_call(
                    message_id=assistant_msg.id,
                    tool_name=tc["name"],
                    arguments=tc.get("args"),
                    result=json.dumps(tc.get("result", ""), ensure_ascii=False)[:500],
                    status="success",
                )
                tool_calls_saved.append({"name": tc["name"], "args": tc.get("args")})

            return {
                "session_id": session_id,
                "answer": result["answer"],
                "tool_calls": tool_calls_saved,
                "usage": result["usage"],
            }

        except Exception as e:
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            logger.error("Chat error: {}", e)
            # Save error as assistant message
            await self.repo.add_message(
                session_id=session_id,
                role="assistant",
                content=f"❌ Ошибка: {e}",
                response_time_ms=int(elapsed),
            )
            return {"session_id": session_id, "answer": f"❌ Ошибка: {e}", "tool_calls": [], "usage": {"prompt_tokens": 0, "completion_tokens": 0}}
