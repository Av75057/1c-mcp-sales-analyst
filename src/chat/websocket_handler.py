from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.chat.repository import ChatRepository
from src.deepseek_client import DeepSeekClient, SYSTEM_PROMPT
from src.logger import logger

router = APIRouter()


@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info("[WS] Connected: session={}", session_id)

    from src.admin.database import async_session

    async with async_session() as db:
        repo = ChatRepository(db)
        deepseek = DeepSeekClient()

        try:
            while True:
                raw = await websocket.receive_text()
                data = json.loads(raw)
                msg_type = data.get("type", "")

                if msg_type == "get_sessions":
                    user_id = "admin"
                    sessions = await repo.list_sessions(user_id=user_id, limit=50)
                    await websocket.send_json({
                        "type": "sessions",
                        "sessions": [
                            {
                                "id": s["id"],
                                "title": s.get("title", "Новый чат"),
                                "created_at": s.get("created_at", ""),
                                "updated_at": s.get("updated_at", ""),
                                "message_count": s.get("messages_count", 0),
                            }
                            for s in sessions
                        ],
                    })

                elif msg_type == "get_messages":
                    sid = data.get("session_id", session_id)
                    msgs, _ = await repo.get_messages(sid, page=1, limit=200)
                    result_messages = []
                    for m in msgs:
                        msg_dict: dict = {
                            "id": str(m.id),
                            "role": m.role,
                            "content": m.content,
                            "timestamp": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
                        }
                        # Load tool calls and reconstruct chart if present
                        try:
                            raw_tool_calls = await repo.get_tool_calls(str(m.id))
                            if raw_tool_calls:
                                tool_calls = []
                                for tc in raw_tool_calls:
                                    tc_entry = {"name": tc.get("tool_name", ""), "args": {}}
                                    try:
                                        tc_entry["args"] = json.loads(tc.get("arguments", "{}"))
                                    except (json.JSONDecodeError, TypeError):
                                        pass
                                    try:
                                        tc_entry["result"] = json.loads(tc.get("result", "{}"))
                                    except (json.JSONDecodeError, TypeError):
                                        tc_entry["result"] = None
                                    tool_calls.append(tc_entry)
                                msg_dict["tool_calls"] = tool_calls
                                # Check for create_chart result
                                chart_tc = next((tc for tc in tool_calls if tc.get("name") == "create_chart"), None)
                                if chart_tc and chart_tc.get("result"):
                                    result_data = chart_tc["result"]
                                    table = result_data.get("table_data", [])
                                    if table:
                                        config = chart_tc.get("args", {})
                                        if not config.get("chart_type") and result_data.get("chart_type"):
                                            config["chart_type"] = result_data["chart_type"]
                                        msg_dict["chart"] = {
                                            "config": config,
                                            "data": table,
                                            "status": "ready",
                                        }
                                        if result_data.get("drilldown"):
                                            msg_dict["chart"]["domain_id"] = result_data.get("domain_id", "")
                                            msg_dict["chart"]["drilldown"] = result_data["drilldown"]
                                        if result_data.get("image_base64"):
                                            msg_dict["chart"]["image_base64"] = result_data["image_base64"]
                        except Exception:
                            logger.warning("[WS] Failed to load tool_calls for msg {}", m.id)
                        result_messages.append(msg_dict)
                    await websocket.send_json({
                        "type": "messages",
                        "messages": result_messages,
                        "id": sid,
                    })

                elif msg_type == "delete_session":
                    sid = data.get("session_id", "")
                    if sid:
                        try:
                            await repo.delete_session(sid)
                            await websocket.send_json({"type": "session_deleted", "id": sid})
                            # Отправляем обновлённый список сессий
                            user_id = "admin"
                            sessions = await repo.list_sessions(user_id=user_id, limit=50)
                            await websocket.send_json({
                                "type": "sessions",
                                "sessions": [
                                    {
                                        "id": s["id"],
                                        "title": s.get("title", "Новый чат"),
                                        "created_at": s.get("created_at", ""),
                                        "updated_at": s.get("updated_at", ""),
                                        "message_count": s.get("messages_count", 0),
                                    }
                                    for s in sessions
                                ],
                            })
                        except Exception as e:
                            logger.warning("[WS] Failed to delete session: {}", e)
                            await websocket.send_json({"type": "error", "content": f"Ошибка удаления: {e}"})

                elif msg_type == "message":
                    content = data.get("content", "")
                    if not content:
                        continue

                    # Create session if new
                    actual_session_id = session_id
                    if actual_session_id == "new" or not actual_session_id:
                        session = await repo.create_session(user_id="admin", title=content[:50])
                        actual_session_id = session.id
                        await websocket.send_json({"type": "session_created", "id": actual_session_id})

                    # Save user message
                    try:
                        await repo.add_message(session_id=actual_session_id, role="user", content=content)
                    except Exception as e:
                        logger.warning("[WS] Failed to save user msg: {}", e)

                    # Build context for AI
                    messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
                    try:
                        history = await repo.get_context_messages(session_id=actual_session_id, max_tokens=3000)
                        messages_for_ai.extend(history)
                    except Exception as e:
                        logger.warning("[WS] Context error: {}", e)
                    messages_for_ai.append({"role": "user", "content": content})

                    # Call DeepSeek
                    try:
                        result = await deepseek.process_query_with_messages(messages_for_ai)
                        answer = result.get("answer", "")
                        tool_calls_list = result.get("tool_calls", [])

                        # Send tool calls
                        try:
                            for tc in tool_calls_list:
                                await websocket.send_json({
                                    "type": "tool_call",
                                    "name": tc.get("name", ""),
                                    "args": tc.get("args", {}),
                                })

                                if tc.get("name") == "create_chart":
                                    args = tc.get("args", {})
                                    result_data = tc.get("result", {})
                                    table = result_data.get("table_data", [])
                                    if table and len(table) > 0:
                                        chart_msg: dict = {
                                            "type": "chart_data",
                                            "config": args,
                                            "data": table,
                                            "image_base64": result_data.get("image_base64", ""),
                                        }
                                        if result_data.get("drilldown"):
                                            chart_msg["domain_id"] = result_data.get("domain_id", "")
                                            chart_msg["drilldown"] = result_data["drilldown"]
                                        await websocket.send_json(chart_msg)
                        except Exception:
                            logger.warning("[WS] Client disconnected during tool calls")
                            break

                        # Stream the answer word by word
                        try:
                            words = answer.split(" ")
                            for i, word in enumerate(words):
                                await websocket.send_json({
                                    "type": "token",
                                    "content": word + (" " if i < len(words) - 1 else ""),
                                })
                                await asyncio.sleep(0.02)
                            await websocket.send_json({"type": "done"})
                        except Exception:
                            logger.warning("[WS] Client disconnected during streaming")
                            break

                        # Save assistant message
                        try:
                            usage = result.get("usage", {})
                            msg_id = await repo.add_message(
                                session_id=actual_session_id,
                                role="assistant",
                                content=answer,
                                tokens_used=usage.get("completion_tokens", 0),
                            )
                            # Save tool calls
                            if msg_id and tool_calls_list:
                                import json as _json
                                for tc in tool_calls_list:
                                    try:
                                        args_dict = tc.get("args", {})
                                        result_str = _json.dumps(tc.get("result", {}), ensure_ascii=False)
                                        await repo.add_tool_call(
                                            message_id=str(msg_id.id),
                                            tool_name=tc.get("name", ""),
                                            arguments=args_dict,
                                            result=result_str,
                                            status="success",
                                        )
                                    except Exception as tce:
                                        logger.warning("[WS] Failed to save tool call: {}", tce)
                        except Exception as e:
                            logger.warning("[WS] Failed to save assistant msg: {}", e)

                    except Exception as e:
                        logger.error("[WS] DeepSeek error: {}", e)
                        await websocket.send_json({"type": "error", "content": f"Ошибка AI: {e!s}"})

        except WebSocketDisconnect:
            logger.info("[WS] Disconnected: session={}", session_id)
        except Exception as e:
            logger.error("[WS] Error: {}", e)
            try:
                await websocket.send_json({"type": "error", "content": str(e)})
            except Exception:
                pass
