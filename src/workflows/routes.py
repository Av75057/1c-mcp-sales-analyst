from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.events.bus import event_bus
from src.workflows.definitions.low_stock import LOW_STOCK_WORKFLOW
from src.workflows.engine import WorkflowEngine

engine = WorkflowEngine(event_bus)
engine.register(LOW_STOCK_WORKFLOW)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("/")
async def list_workflows():
    return {"workflows": engine.get_status()}


@router.get("/log")
async def workflow_log():
    return {"log": engine.execution_log[-100:]}


@router.post("/{name}/run")
async def run_workflow(name: str):
    if name not in engine.workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    from src.events.bus import Event
    await event_bus.publish(Event(event_type="stock_low", data={"quantity": 3, "min_qty": 10, "nomenclature_name": "Test", "nomenclature_id": "test-1"}, source="api"))
    return {"status": "triggered", "workflow": name}
