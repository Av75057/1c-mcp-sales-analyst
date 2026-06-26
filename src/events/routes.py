from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from src.events.bus import Event, event_bus

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("/publish")
async def api_publish_event(body: dict):
    event = Event(event_type=body.get("type", "custom"), data=body.get("data"), source=body.get("source", "api"), user_id=body.get("user_id"))
    await event_bus.publish(event)
    return {"status": "published", "id": event.id, "type": event.type}


@router.get("/dead-letter")
async def api_dead_letter():
    return {"events": event_bus.get_dead_letter()}


@router.post("/dead-letter/replay")
async def api_replay_dead_letter():
    count = await event_bus.replay_dead_letter()
    return {"replayed": count}


@router.get("/stats")
async def api_event_stats():
    return {"handlers": {k: len(v) for k, v in event_bus._handlers.items()}, "dead_letter_count": len(event_bus._dead_letter)}
