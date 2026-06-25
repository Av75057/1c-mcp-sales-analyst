from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.database import get_db
from src.auth.dependencies import get_token_payload
from src.chat.service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_user(request: Request) -> str:
    payload = getattr(request.state, "user", None)
    if payload:
        return payload.sub
    return "anonymous"


@router.get("/sessions")
async def list_sessions(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = _get_user(request)
    svc = ChatService(db)
    sessions = await svc.repo.list_sessions(user_id=user_id)
    return {"sessions": sessions}


@router.post("/sessions")
async def create_session(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = _get_user(request)
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    svc = ChatService(db)
    session = await svc.repo.create_session(user_id=user_id, title=body.get("title", "Новый чат"))
    return {"id": session.id, "title": session.title, "created_at": session.created_at.isoformat()}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    svc = ChatService(db)
    session = await svc.repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"id": session.id, "title": session.title, "created_at": session.created_at.isoformat(), "updated_at": session.updated_at.isoformat(), "is_archived": session.is_archived}


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    svc = ChatService(db)
    ok = await svc.repo.update_session(session_id, **{k: v for k, v in body.items() if k in ("title", "is_archived")})
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Updated"}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    svc = ChatService(db)
    ok = await svc.repo.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Deleted"}


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, page: int = Query(1, ge=1), limit: int = Query(50, le=200), db: AsyncSession = Depends(get_db)):
    svc = ChatService(db)
    messages, total = await svc.repo.get_messages(session_id, page=page, limit=limit)
    msg_list = []
    for m in messages:
        tool_calls = await svc.repo.get_tool_calls(m.id) if m.role == "assistant" else []
        msg_list.append({
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "tokens_used": m.tokens_used,
            "response_time_ms": m.response_time_ms,
            "created_at": m.created_at.isoformat(),
            "tool_calls": tool_calls,
        })
    return {"messages": msg_list, "total": total, "page": page, "pages": max(1, (total + limit - 1) // limit)}


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = _get_user(request)
    content = body.get("content", "")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Message content is required")
    svc = ChatService(db)
    result = await svc.process_message(session_id=session_id, user_id=user_id, content=content)
    return result


@router.delete("/sessions/{session_id}/messages/{message_id}")
async def delete_message(session_id: str, message_id: str, db: AsyncSession = Depends(get_db)):
    svc = ChatService(db)
    ok = await svc.repo.delete_message(message_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Deleted"}


@router.get("/sessions/{session_id}/export")
async def export_session(session_id: str, db: AsyncSession = Depends(get_db)):
    svc = ChatService(db)
    session = await svc.repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages, _ = await svc.repo.get_messages(session_id, page=1, limit=10000)
    result = {"session": {"id": session.id, "title": session.title, "created_at": session.created_at.isoformat()}, "messages": [{"role": m.role, "content": m.content, "tokens_used": m.tokens_used} for m in messages]}
    return result


@router.get("/search")
async def search_messages(q: str = Query(""), session_id: str | None = Query(None), limit: int = Query(50, le=200), request: Request = None, db: AsyncSession = Depends(get_db)):
    if not q.strip():
        return {"results": []}
    user_id = _get_user(request)
    svc = ChatService(db)
    results = await svc.repo.search_messages(user_id=user_id, query=q, session_id=session_id, limit=limit)
    return {"results": results, "total": len(results)}
