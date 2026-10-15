"""Execution CLI commands."""


import typer

from agent_factory.runtime.engine import RuntimeEngine

app = typer.Typer(name="execution", help="Manage executions")


@app.command()
def get(execution_id: str = typer.Argument(..., help="Execution ID")):
    """Get execution details."""
    runtime = RuntimeEngine()
    execution = runtime.get_execution(execution_id)
    
    if not execution:
        typer.echo(f"❌ Execution not found: {execution_id}")
        raise typer.Exit(1)
    
    typer.echo(f"Execution: {execution_id}")
    typer.echo(f"  Type: {execution.type}")
    typer.echo(f"  Entity ID: {execution.entity_id}")
    typer.echo(f"  Status: {execution.status}")
    typer.echo(f"  Created: {execution.created_at}")
    if execution.completed_at:
        typer.echo(f"  Completed: {execution.completed_at}")
    if execution.error:
        typer.echo(f"  Error: {execution.error}")


@app.command()
def list(
    entity_id: str | None = typer.Option(None, "--entity", "-e", help="Filter by entity ID"),
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(10, "--limit", "-l", help="Results limit"),
):
    """List executions."""
    runtime = RuntimeEngine()
    executions = runtime.list_executions(
        entity_id=entity_id,
        status=status,
        limit=limit
    )
    
    if not executions:
        typer.echo("No executions found.")
        return
    
    typer.echo(f"Executions ({len(executions)}):")
    for ex in executions:
        status_icon = "✅" if ex.status == "completed" else "❌" if ex.status == "error" else "⏳"
        typer.echo(f"  {status_icon} {ex.id}: {ex.type}/{ex.entity_id} - {ex.status}")


@app.command()
def retry(execution_id: str = typer.Argument(..., help="Execution ID")):
    """Retry a failed execution."""
    typer.echo("💡 Retry functionality requires API access")
    typer.echo("   Use: POST /api/v1/executions/{execution_id}/retry")


@app.command()
def cancel(execution_id: str = typer.Argument(..., help="Execution ID")):
    """Cancel a running execution."""
    typer.echo("💡 Cancel functionality requires API access")
    typer.echo("   Use: DELETE /api/v1/executions/{execution_id}")
