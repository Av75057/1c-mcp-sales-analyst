from __future__ import annotations

from fastapi import APIRouter, Depends

from src.admin.dependencies import require_admin
from src.admin.services.health_service import HealthService

router = APIRouter(prefix="/admin/integrations", tags=["admin"])


@router.get("/")
async def list_integrations(_=Depends(require_admin)):
    return {
        "services": [
            {"name": "1C УНФ", "description": "Данные о продажах, остатках, клиентах", "endpoints": ["stock", "sales", "purchases", "batch", "documents"]},
            {"name": "DeepSeek API", "description": "AI-аналитика, чат, инсайты", "endpoints": ["chat", "function_calling"]},
            {"name": "Batch Endpoint", "description": "Групповые запросы к 1С", "endpoints": ["/hs/api/v1/batch"]},
        ]
    }


@router.get("/check")
async def check_integrations(_=Depends(require_admin)):
    hs = HealthService()
    return await hs.check_all()


@router.get("/check/1c")
async def check_1c(_=Depends(require_admin)):
    hs = HealthService()
    return await hs.check_1c()


@router.get("/check/deepseek")
async def check_deepseek(_=Depends(require_admin)):
    hs = HealthService()
    return await hs.check_deepseek()


@router.get("/check/batch")
async def check_batch(_=Depends(require_admin)):
    hs = HealthService()
    return await hs.check_batch()
