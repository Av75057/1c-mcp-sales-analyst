from __future__ import annotations

import os

os.environ["TZ"] = "UTC"

import pytest

from src.proactive.scheduler import ScheduledAnalytics


class TestScheduler:
    def test_setup(self):
        s = ScheduledAnalytics()
        s.setup()
        jobs = s.get_jobs()
        assert len(jobs) >= 3

    def test_job_names(self):
        s = ScheduledAnalytics()
        s.setup()
        names = [j["id"] for j in s.get_jobs()]
        assert "morning_report" in names
        assert "check_anomalies" in names
        assert "check_stock" in names

    @pytest.mark.asyncio
    async def test_run_job_morning(self):
        s = ScheduledAnalytics()
        result = await s.run_job("morning_report")
        assert "executed" in result

    @pytest.mark.asyncio
    async def test_unknown_job(self):
        s = ScheduledAnalytics()
        with pytest.raises(ValueError):
            await s.run_job("nonexistent")
