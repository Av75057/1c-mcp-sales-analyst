from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.rag.repository import create_doc, delete_doc, get_doc, init_db, list_docs, search_docs, update_doc, get_stats

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.on_event("startup")
async def startup():
    init_db()


@router.post("/documents")
async def api_create_doc(body: dict):
    doc = create_doc(title=body.get("title", ""), content=body.get("content", ""), doc_type=body.get("document_type", "general"), tags=body.get("tags"), created_by=body.get("created_by", "api"))
    return {"status": "created", **doc}


@router.get("/documents")
async def api_list_docs(document_type: str | None = Query(None), limit: int = Query(100, le=500), offset: int = Query(0)):
    docs = list_docs(doc_type=document_type, limit=limit, offset=offset)
    return {"documents": docs, "total": len(docs)}


@router.get("/documents/{doc_id}")
async def api_get_doc(doc_id: str):
    doc = get_doc(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.put("/documents/{doc_id}")
async def api_update_doc(doc_id: str, body: dict):
    ok = update_doc(doc_id, title=body.get("title"), content=body.get("content"), tags=body.get("tags"))
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "updated", "id": doc_id}


@router.delete("/documents/{doc_id}")
async def api_delete_doc(doc_id: str):
    ok = delete_doc(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted"}


@router.get("/search")
async def api_search_docs(q: str = Query(""), top_k: int = Query(5, le=20)):
    results = search_docs(query=q, limit=top_k)
    return {"results": results, "total": len(results)}


@router.get("/stats")
async def api_knowledge_stats():
    return get_stats()


@router.post("/reindex")
async def api_reindex():
    return {"status": "ok", "message": "Reindex triggered"}
