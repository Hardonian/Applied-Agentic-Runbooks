"""
Scheduler for running agents and workflows on a schedule.
"""

import threading
import time
from collections.abc import Callable
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
        job_id = f"{agent_id}-{schedule_str}"

        def job():
            if run_func:
                run_func(agent_id, input_text)

        # Parse schedule string
        if schedule_str == "daily":
            schedule.every().day.do(job)
        elif schedule_str == "hourly":
            schedule.every().hour.do(job)
        elif schedule_str == "weekly":
            schedule.every().week.do(job)
        else:
            # Assume cron expression (simplified)
            schedule.every().day.at(schedule_str).do(job)

        self.jobs[job_id] = job
        return job_id

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
        job_id = f"{workflow_id}-{schedule_str}"

        def job():
            if run_func:
                run_func(workflow_id, context)

        if schedule_str == "daily":
            schedule.every().day.do(job)
        elif schedule_str == "hourly":
            schedule.every().hour.do(job)
        elif schedule_str == "weekly":
            schedule.every().week.do(job)
        else:
            schedule.every().day.at(schedule_str).do(job)

        self.jobs[job_id] = job
        return job_id

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self.running:
            return

        self.running = True

        def run():
            while self.running:
                schedule.run_pending()
                time.sleep(1)

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
        if self.thread:
            self.thread.join(timeout=5)
