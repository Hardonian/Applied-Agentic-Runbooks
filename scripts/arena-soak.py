"""Concurrent REST/WebSocket soak harness for a running Agent Factory deployment."""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time

import httpx


async def submit(client: httpx.AsyncClient, base_url: str, index: int) -> float:
    started = time.perf_counter()
    response = await client.post(
        f"{base_url}/api/v1/arena/jobs",
        json={
            "suites": ["settler_accounting"],
            "concurrency": 8,
            "trials": 2,
            "mode": "reality" if index % 2 else "deterministic",
        },
    )
    response.raise_for_status()
    location = response.headers["location"]
    for _ in range(600):
        status = await client.get(f"{base_url}{location}")
        status.raise_for_status()
        if status.json()["status"] in {"passed", "failed", "cancelled"}:
            break
        await asyncio.sleep(0.1)
    return time.perf_counter() - started


async def run(base_url: str, runs: int, concurrency: int) -> None:
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(timeout=30, limits=limits) as client:

        async def bounded(index: int) -> float:
            async with semaphore:
                return await submit(client, base_url.rstrip("/"), index)

        durations = await asyncio.gather(*(bounded(index) for index in range(runs)))
    ordered = sorted(durations)
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
    print(
        f"runs={runs} concurrency={concurrency} "
        f"p50={statistics.median(durations):.3f}s p95={p95:.3f}s max={max(durations):.3f}s"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()
    asyncio.run(run(args.base_url, max(1, args.runs), max(1, args.concurrency)))


if __name__ == "__main__":
    main()
