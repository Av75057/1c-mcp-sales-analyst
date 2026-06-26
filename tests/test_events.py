from __future__ import annotations

import pytest

from src.events.bus import Event, EventBus


class TestEvent:
    def test_create(self):
        e = Event("test", {"key": "value"}, "source", "user1")
        assert e.type == "test"
        assert e.data == {"key": "value"}
        assert e.source == "source"
        assert e.user_id == "user1"
        assert e.id is not None


class TestEventBus:
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        bus = EventBus()
        results = []

        async def handler(event):
            results.append(event.data)

        bus.subscribe("test_event", handler)
        await bus.publish(Event("test_event", {"msg": "hello"}))
        assert len(results) == 1
        assert results[0]["msg"] == "hello"

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        bus = EventBus()
        results = []

        async def h1(event):
            results.append("h1")

        async def h2(event):
            results.append("h2")

        bus.subscribe("multi", h1)
        bus.subscribe("multi", h2)
        await bus.publish(Event("multi"))
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_unrelated_events(self):
        bus = EventBus()
        results = []

        async def handler(event):
            results.append(event.data)

        bus.subscribe("type_a", handler)
        await bus.publish(Event("type_b", {"x": 1}))
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_handler_error_goes_to_dead_letter(self):
        bus = EventBus()

        async def failing_handler(event):
            raise ValueError("fail")

        bus.subscribe("failing", failing_handler)
        await bus.publish(Event("failing", {"x": 1}))

        dead = bus.get_dead_letter()
        assert len(dead) == 1
        assert dead[0]["type"] == "failing"

    @pytest.mark.asyncio
    async def test_replay_dead_letter(self):
        bus = EventBus()
        results = []

        async def handler(event):
            results.append(event.data)

        async def failing_handler(event):
            raise ValueError("fail")

        bus.subscribe("good", handler)
        bus.subscribe("bad", failing_handler)

        await bus.publish(Event("bad"))
        assert len(bus.get_dead_letter()) == 1

        bus.subscribe("bad", handler)
        count = await bus.replay_dead_letter()
        assert count == 1

    @pytest.mark.asyncio
    async def test_subscribe_all(self):
        bus = EventBus()
        results = []

        async def h1(event):
            results.append(event.type)

        bus.subscribe_all({"ev1": [h1], "ev2": [h1]})
        await bus.publish(Event("ev1"))
        await bus.publish(Event("ev2"))
        assert len(results) == 2
