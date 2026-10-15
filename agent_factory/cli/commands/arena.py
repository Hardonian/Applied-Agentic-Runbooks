"""CLI commands for the autonomous benchmark arena."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer

from agent_factory.evaluation.arena import ArenaRunner, GauntletSuite
from agent_factory.evaluation.arena.evidence import EvidenceVerifier
from agent_factory.evaluation.arena.service import arena_service

app = typer.Typer(help="Run offline autonomous benchmarks and red-team gauntlets.")


@app.command("run")
def run_command(
    suite: Annotated[list[str] | None, typer.Option("--suite", "-s")] = None,
    concurrency: Annotated[int, typer.Option(min=1, max=1000)] = 32,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    """Run all five suites or one or more selected suites."""
    aliases = {
        "reasoning": GauntletSuite.REASONING_FRONTIER,
        "cascade": GauntletSuite.PARETO_CASCADE,
        "security": GauntletSuite.ADVERSARIAL_SECURITY,
        "healing": GauntletSuite.SELF_HEALING,
        "settler": GauntletSuite.SETTLER_ACCOUNTING,
    }
    selected = [aliases[item] if item in aliases else GauntletSuite(item) for item in suite] if suite else None
    artifact_dir = output.parent if output else None
    summary = asyncio.run(
        ArenaRunner(artifact_dir=artifact_dir).run(selected, concurrency=concurrency)
    )
    payload = summary.to_dict()
    rendered = json.dumps(payload, indent=2)
    if output:
        output.write_text(rendered, encoding="utf-8")
        typer.echo(f"Arena summary written to {output}")
    else:
        typer.echo(rendered)


@app.command("verify")
def verify_command(
    manifest: Annotated[Path, typer.Argument(help="Path to an Arena manifest JSON")],
) -> None:
    """Independently verify a signed Arena evidence bundle offline."""
    report = EvidenceVerifier().verify(manifest)
    typer.echo(json.dumps(report.to_dict(), indent=2))
    if not report.valid:
        raise typer.Exit(1)


@app.command("worker")
def worker_command() -> None:
    """Run the Redis-backed durable Arena worker until interrupted."""
    typer.echo("Starting durable Arena worker")
    try:
        asyncio.run(arena_service.worker_forever())
    except KeyboardInterrupt:
        typer.echo("Arena worker stopped")
