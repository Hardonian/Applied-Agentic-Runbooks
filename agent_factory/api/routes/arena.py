"""REST interface for arena runs and verifiable leaderboards."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agent_factory.api.ws.event_bus import event_bus
from agent_factory.evaluation.arena import ArenaRunner, GauntletSuite

router = APIRouter()
_runs: dict[str, dict[str, Any]] = {}


class ArenaRunRequest(BaseModel):
    """Arena run selection and load settings."""

    suites: list[GauntletSuite] | None = None
    concurrency: int = Field(default=32, ge=1, le=1000)


@router.post("/run")
async def run_arena(request: ArenaRunRequest) -> dict[str, Any]:
    """Execute an offline-capable arena run and return its proof bundle."""
    runner = ArenaRunner()

    async def sink(event: dict[str, Any]) -> None:
        await event_bus.publish("arena", event)

    summary = await runner.run(
        suites=request.suites, concurrency=request.concurrency, event_sink=sink
    )
    payload = summary.to_dict()
    _runs[summary.run_id] = payload
    return payload


@router.get("/leaderboard")
async def arena_leaderboard(limit: int = 20) -> dict[str, Any]:
    """Rank recent runs by pass rate, Pareto score, and p95 latency."""
    bounded_limit = max(1, min(limit, 100))
    ranked = sorted(
        _runs.values(),
        key=lambda run: (
            -float(run["metrics"]["pass_rate"]),
            -float(run["metrics"]["pareto_frontier_score"]),
            float(run["metrics"]["p95_latency_ms"]),
        ),
    )[:bounded_limit]
    entries = [
        {
            "rank": index,
            "run_id": run["run_id"],
            "status": run["status"],
            **run["metrics"],
            "merkle_root": run["veridag_proof"]["final_merkle_root"],
        }
        for index, run in enumerate(ranked, start=1)
    ]
    return {"entries": entries, "total_runs": len(_runs)}
