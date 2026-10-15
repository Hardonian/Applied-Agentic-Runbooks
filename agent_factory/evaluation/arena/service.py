"""Asynchronous durable orchestration service for Arena jobs."""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_factory.api.ws.event_bus import event_bus
from agent_factory.evaluation.arena.repository import ArenaRepository
from agent_factory.evaluation.arena.runner import ArenaRunCancelled, ArenaRunner
from agent_factory.jobs.queue import Job, JobStatus, RedisJobQueue


class ArenaService:
    """Coordinate durable records, background tasks, cancellation, and event delivery."""

    def __init__(self, repository: ArenaRepository | None = None) -> None:
        self.repository = repository or ArenaRepository(
            retention_days=int(os.getenv("ARENA_RETENTION_DAYS", "30"))
        )
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self.artifact_dir = Path(os.getenv("ARENA_ARTIFACT_DIR", "artifacts/arena"))
        self.job_backend = os.getenv("ARENA_JOB_BACKEND", "local")
        self.job_queue: RedisJobQueue | None = None
        if self.job_backend == "redis":
            self.job_queue = RedisJobQueue(key_prefix="arena_jobs:")

    async def submit(
        self,
        request: dict[str, Any],
        *,
        tenant_id: str = "public",
        created_by: str | None = None,
    ) -> dict[str, Any]:
        # Bound database growth without requiring an external housekeeping process.
        await asyncio.to_thread(self.repository.purge_expired)
        run_id = f"arena-{uuid.uuid4().hex[:12]}"
        record = await asyncio.to_thread(
            self.repository.create,
            run_id,
            request,
            tenant_id=tenant_id,
            created_by=created_by,
            mode=str(request.get("mode", "deterministic")),
        )
        if self.job_queue is not None:
            await asyncio.to_thread(
                self.job_queue.enqueue,
                Job(
                    id=run_id,
                    job_type="arena",
                    payload={"tenant_id": tenant_id, "request": request},
                    max_retries=3,
                ),
            )
        else:
            task = asyncio.create_task(self._execute(run_id, tenant_id, request))
            self._tasks[run_id] = task

            def discard(_task: asyncio.Task[None]) -> None:
                self._tasks.pop(run_id, None)

            task.add_done_callback(discard)
        return record

    async def run_inline(
        self,
        request: dict[str, Any],
        *,
        tenant_id: str = "public",
        created_by: str | None = None,
    ) -> dict[str, Any]:
        run_id = f"arena-{uuid.uuid4().hex[:12]}"
        record = await asyncio.to_thread(
            self.repository.create,
            run_id,
            request,
            tenant_id=tenant_id,
            created_by=created_by,
            mode=str(request.get("mode", "deterministic")),
        )
        await self._execute(run_id, tenant_id, request)
        return await asyncio.to_thread(self.repository.get, run_id, tenant_id) or record

    async def cancel(self, run_id: str, tenant_id: str = "public") -> bool:
        requested = await asyncio.to_thread(self.repository.request_cancel, run_id, tenant_id)
        if requested:
            await event_bus.publish(
                f"arena:{run_id}",
                {"type": "arena.cancel.requested", "data": {"run_id": run_id}},
            )
        return requested

    async def _execute(self, run_id: str, tenant_id: str, request: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await asyncio.to_thread(
            self.repository.update, run_id, tenant_id, status="running", started_at=now
        )

        async def sink(event: dict[str, Any]) -> None:
            await event_bus.publish("arena", event)
            await event_bus.publish(f"arena:{run_id}", event)

        def cancelled() -> bool:
            record = self.repository.get(run_id, tenant_id)
            return bool(record and record["cancel_requested"])

        try:
            runner = ArenaRunner(artifact_dir=self.artifact_dir)
            summary = await asyncio.wait_for(
                runner.run(
                    suites=request.get("suites"),
                    concurrency=int(request.get("concurrency", 32)),
                    trials=int(request.get("trials", 1)),
                    mode=str(request.get("mode", "deterministic")),
                    run_id=run_id,
                    cancel_check=cancelled,
                    event_sink=sink,
                ),
                timeout=float(request.get("timeout_seconds", 900)),
            )
            await asyncio.to_thread(
                self.repository.update,
                run_id,
                tenant_id,
                status=summary.status,
                summary=summary.to_dict(),
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            from agent_factory.monitoring.metrics import MetricsCollector

            MetricsCollector.record_arena_run(
                summary.status,
                str(request.get("mode", "deterministic")),
                summary.completed_at - summary.started_at,
                summary.metrics["total_cost_usd"],
                summary.metrics["pass_rate"],
            )
        except ArenaRunCancelled:
            await asyncio.to_thread(
                self.repository.update,
                run_id,
                tenant_id,
                status="cancelled",
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        except TimeoutError:
            await self._fail(run_id, tenant_id, "Arena run exceeded its timeout")
        except Exception as exc:  # noqa: BLE001
            await self._fail(run_id, tenant_id, str(exc))

    async def _fail(self, run_id: str, tenant_id: str, error: str) -> None:
        await asyncio.to_thread(
            self.repository.update,
            run_id,
            tenant_id,
            status="failed",
            error=error,
            completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        await event_bus.publish(
            f"arena:{run_id}",
            {"type": "arena.failed", "data": {"run_id": run_id, "error": error}},
        )

    async def execute_queued_once(self) -> bool:
        """Claim and execute one Redis-backed Arena job."""
        if self.job_queue is None:
            return False
        await asyncio.to_thread(self.job_queue.requeue_expired, "arena")
        job = await asyncio.to_thread(self.job_queue.dequeue, "arena")
        if job is None:
            return False
        try:
            await self._execute(
                job.id,
                str(job.payload.get("tenant_id", "public")),
                dict(job.payload.get("request", {})),
            )
            record = self.repository.get(job.id, str(job.payload.get("tenant_id", "public")))
            job.status = (
                JobStatus.COMPLETED if record and record["status"] == "passed" else JobStatus.FAILED
            )
            job.result = record
        except Exception as exc:  # noqa: BLE001
            job.status = JobStatus.FAILED
            job.error = str(exc)
        job.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await asyncio.to_thread(self.job_queue.update_job, job)
        return True

    async def worker_forever(self, poll_seconds: float = 0.25) -> None:
        """Run a crash-isolated Redis worker loop for Kubernetes/Compose workers."""
        if self.job_queue is None:
            raise RuntimeError("ARENA_JOB_BACKEND must be redis for worker mode")
        while True:
            processed = await self.execute_queued_once()
            if not processed:
                await asyncio.sleep(poll_seconds)


arena_service = ArenaService()
