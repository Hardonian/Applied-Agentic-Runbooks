"""CLI commands for the autonomous benchmark arena."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer

from agent_factory.evaluation.arena import ArenaRunner, GauntletSuite

app = typer.Typer(help="Run offline autonomous benchmarks and red-team gauntlets.")


@app.command("run")
def run_command(
    suite: list[str] | None = typer.Option(None, "--suite", "-s"),
    concurrency: int = typer.Option(32, min=1, max=1000),
    output: Path | None = typer.Option(None, "--output", "-o"),
) -> None:
    """Run all five suites or one or more selected suites."""
    selected = [GauntletSuite(item) for item in suite] if suite else None
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
