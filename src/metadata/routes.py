from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.metadata.service import metadata_service

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.get("/config")
async def metadata_config():
    return await metadata_service.get_config()


@router.get("/describe")
async def metadata_describe(object_type: str | None = Query(None), search: str | None = Query(None)):
    objects = await metadata_service.describe(object_type=object_type, search=search)
    return {"objects": objects, "total": len(objects)}


@router.get("/structure/{object_name}")
async def metadata_structure(object_name: str):
    structure = await metadata_service.get_structure(object_name)
    return structure


@router.post("/cache/invalidate")
async def metadata_cache_invalidate():
    count = await metadata_service.invalidate_cache()
    return {"status": "ok", "invalidated": count}
