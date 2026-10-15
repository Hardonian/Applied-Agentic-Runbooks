"""Durable REST interface for Arena jobs, evidence, comparisons, and leaderboards."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from agent_factory.evaluation.arena import GauntletSuite
from agent_factory.evaluation.arena.service import arena_service
from agent_factory.security.auth import get_current_user_from_request

router = APIRouter()


class ArenaRunRequest(BaseModel):
    """Arena suite, load, statistics, and execution-mode settings."""

    suites: list[GauntletSuite] | None = None
    concurrency: int = Field(default=32, ge=1, le=1000)
    trials: int = Field(default=1, ge=1, le=100)
    mode: Literal["deterministic", "reality"] = "deterministic"
    timeout_seconds: float = Field(default=900, ge=1, le=3600)


async def _principal(request: Request) -> tuple[str, str | None]:
    user = await get_current_user_from_request(request)
    if user is None:
        return "public", None
    return user.tenant_id or "public", user.id


@router.post("/run")
async def run_arena(request: ArenaRunRequest, http_request: Request) -> dict[str, Any]:
    """Compatibility endpoint that waits for completion while persisting the run."""
    tenant_id, user_id = await _principal(http_request)
    record = await arena_service.run_inline(
        request.model_dump(mode="json"), tenant_id=tenant_id, created_by=user_id
    )
    summary = record.get("summary")
    if summary is None:
        raise HTTPException(status_code=500, detail=record.get("error") or "Arena run failed")
    return cast(dict[str, Any], summary)


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_arena_job(request: ArenaRunRequest, http_request: Request) -> JSONResponse:
    """Queue a durable background run and return immediately with discovery links."""
    tenant_id, user_id = await _principal(http_request)
    record = await arena_service.submit(
        request.model_dump(mode="json"), tenant_id=tenant_id, created_by=user_id
    )
    run_id = record["run_id"]
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        headers={"Location": f"/api/v1/arena/runs/{run_id}"},
        content={
            **record,
            "status_url": f"/api/v1/arena/runs/{run_id}",
            "events_topic": f"arena:{run_id}",
        },
    )


@router.get("/runs")
async def list_arena_runs(
    http_request: Request, limit: int = 50, run_status: str | None = None
) -> dict[str, Any]:
    """Return durable tenant history newest-first."""
    tenant_id, _ = await _principal(http_request)
    entries = await _to_thread_list(tenant_id, limit, run_status)
    return {"entries": entries, "count": len(entries)}


async def _to_thread_list(
    tenant_id: str, limit: int, run_status: str | None
) -> list[dict[str, Any]]:
    import asyncio

    return await asyncio.to_thread(
        arena_service.repository.list, tenant_id, limit=limit, status=run_status
    )


@router.get("/runs/{run_id}")
async def get_arena_run(run_id: str, http_request: Request) -> dict[str, Any]:
    """Get current lifecycle state and summary for a durable run."""
    import asyncio

    tenant_id, _ = await _principal(http_request)
    record = await asyncio.to_thread(arena_service.repository.get, run_id, tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Arena run not found")
    return record


@router.post("/runs/{run_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_arena_run(run_id: str, http_request: Request) -> dict[str, Any]:
    """Request cooperative cancellation at the next suite boundary."""
    tenant_id, _ = await _principal(http_request)
    if not await arena_service.cancel(run_id, tenant_id):
        raise HTTPException(status_code=409, detail="Run cannot be cancelled")
    return {"run_id": run_id, "status": "cancellation_requested"}


@router.get("/runs/{run_id}/artifacts/{kind}")
async def download_arena_artifact(
    run_id: str, kind: Literal["apcap", "veridag", "manifest"], http_request: Request
) -> FileResponse:
    """Download a persisted proof or packet capture without accepting arbitrary paths."""
    record = await get_arena_run(run_id, http_request)
    summary = record.get("summary") or {}
    candidate = (summary.get("artifact_paths") or {}).get(kind)
    if not candidate:
        raise HTTPException(status_code=404, detail="Artifact not available")
    root = arena_service.artifact_dir.resolve()
    path = Path(candidate).resolve()
    if path != root and root not in path.parents:
        raise HTTPException(status_code=400, detail="Invalid artifact path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    media_type = "application/octet-stream" if kind == "apcap" else "application/json"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.get("/compare")
async def compare_arena_runs(ids: str, http_request: Request) -> dict[str, Any]:
    """Compare up to ten runs across quality, tail latency, cost, and velocity."""
    import asyncio

    tenant_id, _ = await _principal(http_request)
    run_ids = list(dict.fromkeys(item.strip() for item in ids.split(",") if item.strip()))[:10]
    records = await asyncio.gather(
        *(asyncio.to_thread(arena_service.repository.get, run_id, tenant_id) for run_id in run_ids)
    )
    entries = []
    for record in records:
        if record and record.get("summary"):
            summary = record["summary"]
            entries.append(
                {
                    "run_id": record["run_id"],
                    "mode": record["mode"],
                    "status": record["status"],
                    **summary["metrics"],
                }
            )
    return {"entries": entries, "count": len(entries)}


@router.get("/leaderboard")
async def arena_leaderboard(http_request: Request, limit: int = 20) -> dict[str, Any]:
    """Rank persisted tenant runs by pass rate, Pareto score, then p95 latency."""
    tenant_id, _ = await _principal(http_request)
    records = await _to_thread_list(tenant_id, 200, None)
    completed = [record for record in records if record.get("summary")]
    ranked = sorted(
        completed,
        key=lambda record: (
            -float(record["summary"]["metrics"]["pass_rate"]),
            -float(record["summary"]["metrics"]["pareto_frontier_score"]),
            float(record["summary"]["metrics"]["p95_latency_ms"]),
        ),
    )[: max(1, min(limit, 100))]
    entries = [
        {
            "rank": index,
            "run_id": record["run_id"],
            "status": record["status"],
            "mode": record["mode"],
            **record["summary"]["metrics"],
            "merkle_root": record["summary"]["veridag_proof"]["final_merkle_root"],
        }
        for index, record in enumerate(ranked, start=1)
    ]
    return {"entries": entries, "count": len(entries), "total_runs": len(completed)}
