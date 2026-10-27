"""Tests for runtime scheduler."""

from unittest.mock import Mock

import pytest

from agent_factory.runtime.scheduler import Scheduler


@pytest.mark.unit
def test_schedule_agent():
    """Test scheduling an agent."""
    scheduler = Scheduler()
    run_func = Mock()

    job_id = scheduler.schedule_agent(
        agent_id="test-agent", input_text="test input", schedule_str="hourly", run_func=run_func
    )

    assert job_id == "agent:test-agent:hourly"
    assert job_id in scheduler.jobs


@pytest.mark.unit
def test_schedule_workflow():
    """Test scheduling a workflow."""
    scheduler = Scheduler()
    run_func = Mock()

    job_id = scheduler.schedule_workflow(
        workflow_id="test-workflow",
        context={"key": "value"},
        schedule_str="daily",
        run_func=run_func,
    )

    assert job_id == "workflow:test-workflow:daily"
    assert job_id in scheduler.jobs


@pytest.mark.unit
def test_start_stop_scheduler():
    """Test starting and stopping scheduler."""
    scheduler = Scheduler()

    assert not scheduler.running
    scheduler.start()
    assert scheduler.running

    scheduler.stop()
    assert not scheduler.running


@pytest.mark.unit
def test_scheduler_replaces_and_cancels_only_its_own_job():
    scheduler = Scheduler()
    job_id = scheduler.schedule_agent("test-agent", "input", "daily", Mock())
    scheduler.schedule_agent("test-agent", "input", "daily", Mock())

    assert len(scheduler.jobs) == 1
    assert scheduler.cancel(job_id) is True
    assert scheduler.cancel(job_id) is False


@pytest.mark.unit
def test_scheduler_rejects_invalid_schedule():
    with pytest.raises(ValueError, match="schedule_str must be"):
        Scheduler().schedule_agent("test-agent", "input", "every minute", Mock())
