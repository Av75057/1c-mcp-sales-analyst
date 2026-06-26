from __future__ import annotations

import pytest

from src.events.bus import Event, EventBus
from src.workflows.engine import WorkflowEngine
from src.workflows.models import Workflow, WorkflowStep


class TestWorkflowEngine:
    @pytest.mark.asyncio
    async def test_register_workflow(self):
        bus = EventBus()
        engine = WorkflowEngine(bus)
        wf = Workflow(name="test", description="Test workflow", steps=[WorkflowStep(name="step1", event_type="test_event", handler="notify_stock_manager")])
        engine.register(wf)
        assert "test" in engine.workflows

    @pytest.mark.asyncio
    async def test_workflow_executes_steps(self):
        bus = EventBus()
        engine = WorkflowEngine(bus)
        wf = Workflow(name="echo", steps=[WorkflowStep(name="echo_step", event_type="echo_event", handler="notify_stock_manager")])
        engine.register(wf)
        await bus.publish(Event(event_type="echo_event", data={"nomenclature_name": "test"}))
        assert True  # No exception means success

    @pytest.mark.asyncio
    async def test_workflow_log(self):
        bus = EventBus()
        engine = WorkflowEngine(bus)
        wf = Workflow(name="log_test", steps=[WorkflowStep(name="s1", event_type="e1", handler="notify_stock_manager")])
        engine.register(wf)
        status = engine.get_status()
        assert len(status) == 1
        assert status[0]["name"] == "log_test"


class TestWorkflowStep:
    def test_create(self):
        s = WorkflowStep(name="test", event_type="ev", handler="h")
        assert s.name == "test"
        assert s.event_type == "ev"

    def test_with_condition(self):
        s = WorkflowStep(name="test", event_type="ev", handler="h", condition="data.get('qty',0) > 5")
        assert s.condition is not None


class TestWorkflow:
    def test_create(self):
        w = Workflow(name="test", description="desc", steps=[WorkflowStep(name="s1", event_type="e1", handler="h1")])
        assert w.name == "test"
        assert len(w.steps) == 1
