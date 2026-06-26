from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.proactive.scheduler import scheduler

router = APIRouter(prefix="/api/proactive", tags=["proactive"])


@router.post("/start")
async def start_scheduler():
    scheduler.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_scheduler():
    scheduler.stop()
    return {"status": "stopped"}


@router.get("/schedule")
async def get_schedule():
    return {"jobs": scheduler.get_jobs()}


@router.post("/schedule/{job_id}/run")
async def run_job(job_id: str):
    try:
        result = await scheduler.run_job(job_id)
        return {"status": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reports/morning")
async def morning_report():
    await scheduler.morning_report()
    return {"status": "generated"}
