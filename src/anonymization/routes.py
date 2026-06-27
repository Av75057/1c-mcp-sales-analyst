from __future__ import annotations

from fastapi import APIRouter

from src.anonymization.storage import get_stats

router = APIRouter(prefix="/api/anonymization", tags=["anonymization"])


@router.get("/stats")
async def anonymization_stats():
    return get_stats()
