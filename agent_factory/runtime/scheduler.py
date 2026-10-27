"""
Scheduler for running agents and workflows on a schedule.
"""

import threading
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

import schedule


class Scheduler:
    """
    Scheduler for running agents and workflows on a schedule.

    Example:
        >>> scheduler = Scheduler()
        >>> scheduler.schedule_agent("agent-id", "input", schedule="daily")
        >>> scheduler.start()
    """

    def __init__(self):
        """Initialize scheduler."""
        self.jobs: dict[str, Callable] = {}
        self._scheduled_jobs: dict[str, schedule.Job] = {}
        # Do not use schedule's process-global default scheduler: stopping one
        # tenant/application scheduler must not clear another scheduler's jobs.
        self._scheduler = schedule.Scheduler()
        self.running = False
        self.thread: threading.Thread | None = None

    def schedule_agent(
        self,
        agent_id: str,
        input_text: str,
        schedule_str: str = "daily",
        run_func: Callable | None = None,
    ) -> str:
        """
        Schedule an agent to run on a schedule.

        Args:
            agent_id: Agent ID to run
            input_text: Input text for agent
            schedule_str: Schedule string ("daily", "hourly", "weekly", cron expression)
            run_func: Function to call (should run the agent)

        Returns:
            Job ID
        """
        job_id = f"agent:{agent_id}:{schedule_str}"

        def job():
            if run_func:
                run_func(agent_id, input_text)

        return self._register_job(job_id, schedule_str, job)

    def schedule_workflow(
        self,
        workflow_id: str,
        context: dict[str, Any],
        schedule_str: str = "daily",
        run_func: Callable | None = None,
    ) -> str:
        """
        Schedule a workflow to run on a schedule.

        Args:
            workflow_id: Workflow ID to run
            context: Initial context
            schedule_str: Schedule string
            run_func: Function to call

        Returns:
            Job ID
        """
        job_id = f"workflow:{workflow_id}:{schedule_str}"

        def job():
            if run_func:
                run_func(workflow_id, context)

        return self._register_job(job_id, schedule_str, job)

    def _register_job(self, job_id: str, schedule_str: str, job: Callable) -> str:
        """Register a uniquely identified schedule after validating its form."""
        if job_id in self._scheduled_jobs:
            self._scheduler.cancel_job(self._scheduled_jobs[job_id])

        if schedule_str == "daily":
            scheduled_job = self._scheduler.every().day.do(job)
        elif schedule_str == "hourly":
            scheduled_job = self._scheduler.every().hour.do(job)
        elif schedule_str == "weekly":
            scheduled_job = self._scheduler.every().week.do(job)
        else:
            try:
                datetime.strptime(schedule_str, "%H:%M")
            except ValueError as exc:
                raise ValueError(
                    "schedule_str must be daily, hourly, weekly, or HH:MM (24-hour time)"
                ) from exc
            scheduled_job = self._scheduler.every().day.at(schedule_str).do(job)

        self.jobs[job_id] = job
        self._scheduled_jobs[job_id] = scheduled_job
        return job_id

    def cancel(self, job_id: str) -> bool:
        """Cancel one scheduled job without affecting other scheduler instances."""
        scheduled_job = self._scheduled_jobs.pop(job_id, None)
        self.jobs.pop(job_id, None)
        if scheduled_job is None:
            return False
        self._scheduler.cancel_job(scheduled_job)
        return True

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self.running:
            return

        self.running = True

        def run():
            while self.running:
                self._scheduler.run_pending()
                time.sleep(1)

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        self._scheduler.clear()
        self.jobs.clear()
        self._scheduled_jobs.clear()
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
