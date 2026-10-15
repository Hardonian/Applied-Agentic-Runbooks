"""
CLI commands for prompt logging, replay, and diff.
"""


import typer

from agent_factory.promptlog import SQLiteStorage, diff_runs, replay_run

app = typer.Typer(name="promptlog", help="Prompt logging, replay, and diff commands")

# Global storage instance
_storage = None


def get_storage() -> SQLiteStorage:
    """Get or create storage instance."""
    global _storage
    if _storage is None:
        _storage = SQLiteStorage()
    return _storage


@app.command()
def list_runs(
    agent_id: str | None = typer.Option(None, "--agent", help="Filter by agent ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of runs to show"),
):
    """List recent runs."""
    storage = get_storage()
    
    filters = {}
    if agent_id:
        filters["agent_id"] = agent_id
    
    runs = storage.list_runs(filters=filters, limit=limit)
    
    if not runs:
        typer.echo("No runs found.")
        return
    
    typer.echo(f"\nFound {len(runs)} runs:\n")
    for run in runs:
        typer.echo(f"  {run.run_id}")
        typer.echo(f"    Agent: {run.agent_id or 'N/A'}")
        typer.echo(f"    Status: {run.status}")
        typer.echo(f"    Time: {run.execution_time:.2f}s")
        typer.echo(f"    Tokens: {run.tokens_used}")
        typer.echo()


@app.command()
def replay(
    run_id: str = typer.Argument(..., help="Run ID to replay"),
    config_override: str | None = typer.Option(None, "--config", help="Config override file"),
):
    """Replay a run with optional configuration overrides."""
    storage = get_storage()
    
    # Load config override if provided
    config_override_dict = None
    if config_override:
        import yaml
        with open(config_override, "r") as f:
            config_override_dict = yaml.safe_load(f)
    
    try:
        new_run = replay_run(run_id, storage, config_override_dict)
        typer.echo(f"✅ Replayed run: {new_run.run_id}")
        typer.echo(f"   Status: {new_run.status}")
        typer.echo(f"   Execution time: {new_run.execution_time:.2f}s")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def diff(
    run_id_1: str = typer.Argument(..., help="First run ID"),
    run_id_2: str = typer.Argument(..., help="Second run ID"),
):
    """Compare two runs."""
    storage = get_storage()
    
    try:
        diff_result = diff_runs(run_id_1, run_id_2, storage)
        
        typer.echo("\nComparing runs:")
        typer.echo(f"  Run 1: {run_id_1}")
        typer.echo(f"  Run 2: {run_id_2}\n")
        
        typer.echo("Metrics:")
        for metric, values in diff_result["metrics_diff"].items():
            typer.echo(f"  {metric}:")
            typer.echo(f"    Run 1: {values['run1']}")
            typer.echo(f"    Run 2: {values['run2']}")
            typer.echo(f"    Diff: {values['diff']}")
        
        typer.echo(f"\nOutput similarity: {diff_result['output_diff']['similarity']:.2%}")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)
