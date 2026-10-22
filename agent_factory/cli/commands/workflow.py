"""Workflow CLI commands."""

import json

import typer

from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.runtime.engine import RuntimeEngine
from agent_factory.workflows.model import Workflow, WorkflowStep

app = typer.Typer(name="workflow", help="Manage workflows")


@app.command()
def create(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    name: str = typer.Option(..., "--name", "-n", help="Workflow name"),
    steps_file: str = typer.Option(..., "--steps", "-s", help="Path to steps JSON file"),
):
    """Create a new workflow."""
    # Load steps from file
    with open(steps_file) as f:
        steps_data = json.load(f)

    steps = []
    for step_data in steps_data:
        step = WorkflowStep(
            id=step_data["id"],
            agent_id=step_data["agent_id"],
            input_mapping=step_data.get("input_mapping", {}),
            output_mapping=step_data.get("output_mapping", {}),
        )
        steps.append(step)

    workflow = Workflow(
        id=workflow_id,
        name=name,
        steps=steps,
    )

    registry = LocalRegistry()
    registry.register_workflow(workflow)

    runtime = RuntimeEngine()
    runtime.register_workflow(workflow)

    typer.echo(f"✅ Created workflow: {workflow_id}")


@app.command()
def list():
    """List all workflows."""
    registry = LocalRegistry()
    workflows = registry.list_workflows()

    if not workflows:
        typer.echo("No workflows found.")
        return

    typer.echo("Workflows:")
    for workflow_id in workflows:
        workflow = registry.get_workflow(workflow_id)
        if workflow:
            typer.echo(f"  - {workflow_id}: {workflow.name}")
        else:
            typer.echo(f"  - {workflow_id}")


@app.command()
def run(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    context_file: str | None = typer.Option(
        None, "--context", "-c", help="Path to context JSON file"
    ),
):
    """Run a workflow."""
    import json

    registry = LocalRegistry()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        typer.echo(f"❌ Workflow not found: {workflow_id}")
        raise typer.Exit(1)

    # Load context
    if context_file:
        with open(context_file) as f:
            context = json.load(f)
    else:
        context = {}

    runtime = RuntimeEngine()
    # Register workflow with runtime
    runtime.register_workflow(workflow)

    execution_id = runtime.run_workflow(workflow_id, context)

    typer.echo(f"✅ Started workflow execution: {execution_id}")
    typer.echo(f"💡 Check status: agent-factory execution get {execution_id}")


@app.command()
def update(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    name: str | None = typer.Option(None, "--name", "-n", help="Workflow name"),
    steps_file: str | None = typer.Option(None, "--steps", "-s", help="Path to steps JSON file"),
):
    """Update a workflow."""
    registry = LocalRegistry()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        typer.echo(f"❌ Workflow not found: {workflow_id}")
        raise typer.Exit(1)

    if name:
        workflow.name = name

    if steps_file:
        with open(steps_file) as f:
            steps_data = json.load(f)

        from agent_factory.workflows.model import Condition, WorkflowStep

        steps = []
        for step_data in steps_data:
            condition = None
            if step_data.get("condition"):
                cond_data = step_data["condition"]
                condition = Condition(
                    expression=cond_data.get("expression", ""),
                    description=cond_data.get("description"),
                )

            step = WorkflowStep(
                id=step_data["id"],
                agent_id=step_data["agent_id"],
                input_mapping=step_data.get("input_mapping", {}),
                output_mapping=step_data.get("output_mapping", {}),
                condition=condition,
                timeout=step_data.get("timeout", 30),
                retry_attempts=step_data.get("retry_attempts", 3),
            )
            steps.append(step)

        workflow.steps = steps

    registry.register_workflow(workflow)

    runtime = RuntimeEngine()
    runtime.register_workflow(workflow)

    typer.echo(f"✅ Updated workflow: {workflow_id}")


@app.command()
def delete(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
):
    """Delete a workflow."""
    registry = LocalRegistry()
    workflow_file = registry.base_path / "workflows" / f"{workflow_id}.json"

    if not workflow_file.exists():
        typer.echo(f"❌ Workflow not found: {workflow_id}")
        raise typer.Exit(1)

    workflow_file.unlink()
    typer.echo(f"✅ Deleted workflow: {workflow_id}")


@app.command()
def status(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
):
    """Get workflow status."""
    registry = LocalRegistry()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        typer.echo(f"❌ Workflow not found: {workflow_id}")
        raise typer.Exit(1)

    runtime = RuntimeEngine()
    executions = runtime.list_executions(entity_id=workflow_id, limit=5)

    typer.echo(f"Workflow: {workflow.name} ({workflow_id})")
    typer.echo(f"Steps: {len(workflow.steps)}")
    typer.echo("\nRecent Executions:")

    if not executions:
        typer.echo("  No executions found.")
    else:
        for ex in executions:
            status_icon = (
                "✅" if ex.status == "completed" else "❌" if ex.status == "error" else "⏳"
            )
            typer.echo(f"  {status_icon} {ex.id}: {ex.status}")


@app.command()
def trigger(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    context_file: str | None = typer.Option(
        None, "--context", "-c", help="Path to context JSON file"
    ),
):
    """Trigger a workflow manually."""
    import json

    registry = LocalRegistry()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        typer.echo(f"❌ Workflow not found: {workflow_id}")
        raise typer.Exit(1)

    # Load context
    if context_file:
        with open(context_file) as f:
            context = json.load(f)
    else:
        context = {}

    runtime = RuntimeEngine()
    runtime.register_workflow(workflow)

    execution_id = runtime.run_workflow(workflow_id, context)

    typer.echo(f"✅ Triggered workflow execution: {execution_id}")


@app.command()
def visualize(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
    format: str = typer.Option(
        "mermaid", "--format", "-f", help="Output format (mermaid or graphviz)"
    ),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Visualize a workflow as a diagram."""
    from agent_factory.workflows.visualizer import visualize as visualize_workflow

    registry = LocalRegistry()
    workflow = registry.get_workflow(workflow_id)

    if not workflow:
        typer.echo(f"❌ Workflow not found: {workflow_id}")
        raise typer.Exit(1)

    try:
        content = visualize_workflow(workflow, format=format, output_path=output)

        if output:
            typer.echo(f"✅ Visualization saved to: {output}")
        else:
            typer.echo("\n" + content)
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1) from e
