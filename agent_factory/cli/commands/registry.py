"""Registry CLI commands."""

from pathlib import Path

import typer

from agent_factory.agents.agent import Agent
from agent_factory.blueprints.model import Blueprint
from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.tools.base import Tool

app = typer.Typer(name="registry", help="Manage registry")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    category: str | None = typer.Option(None, "--category", "-c", help="Category filter"),
):
    """Search the registry."""
    registry = LocalRegistry()
    results = registry.search(query, category=category)

    typer.echo(f"Search results for: {query}")

    if results.get("agents"):
        typer.echo(f"\nAgents ({len(results['agents'])}):")
        for agent_id in results["agents"]:
            agent = registry.get_agent(agent_id)
            if agent:
                typer.echo(f"  - {agent_id}: {agent.name}")
            else:
                typer.echo(f"  - {agent_id}")

    if results.get("tools"):
        typer.echo(f"\nTools ({len(results['tools'])}):")
        for tool_id in results["tools"]:
            tool = registry.get_tool(tool_id)
            if tool:
                typer.echo(f"  - {tool_id}: {tool.name}")
            else:
                typer.echo(f"  - {tool_id}")

    if results.get("workflows"):
        typer.echo(f"\nWorkflows ({len(results['workflows'])}):")
        for workflow_id in results["workflows"]:
            workflow = registry.get_workflow(workflow_id)
            if workflow:
                typer.echo(f"  - {workflow_id}: {workflow.name}")
            else:
                typer.echo(f"  - {workflow_id}")

    if results.get("blueprints"):
        typer.echo(f"\nBlueprints ({len(results['blueprints'])}):")
        for blueprint_id in results["blueprints"]:
            blueprint = registry.get_blueprint(blueprint_id)
            if blueprint:
                typer.echo(f"  - {blueprint_id}: {blueprint.name}")
            else:
                typer.echo(f"  - {blueprint_id}")


@app.command()
def install(
    resource_type: str = typer.Argument(
        ..., help="Resource type: agent, tool, workflow, blueprint"
    ),
    resource_id: str = typer.Argument(..., help="Resource ID"),
    source_path: str | None = typer.Option(
        None, "--source", "-s", help="Source path for installation"
    ),
):
    """Install a resource from registry."""
    registry = LocalRegistry()

    if resource_type == "agent":
        if source_path:
            import json

            agent_data = json.loads(Path(source_path).read_text())
            agent = Agent.from_dict(agent_data)
            registry.register_agent(agent)
            typer.echo(f"✅ Installed agent: {resource_id}")
        else:
            typer.echo("❌ Source path required for agent installation")
            raise typer.Exit(1)
    elif resource_type == "tool":
        if source_path:
            import json

            tool_data = json.loads(Path(source_path).read_text())

            # Create placeholder tool
            def placeholder(**kwargs):
                raise NotImplementedError("Tool implementation not available")

            tool = Tool(
                id=tool_data.get("id", resource_id),
                name=tool_data.get("name", resource_id),
                description=tool_data.get("description", ""),
                implementation=placeholder,
            )
            registry.register_tool(tool)
            typer.echo(f"✅ Installed tool: {resource_id}")
        else:
            typer.echo("❌ Source path required for tool installation")
            raise typer.Exit(1)
    elif resource_type == "workflow":
        if source_path:
            import json

            json.loads(Path(source_path).read_text())
            workflow = registry.get_workflow(resource_id)
            if not workflow:
                typer.echo("❌ Workflow reconstruction requires agents registry")
                raise typer.Exit(1)
            typer.echo(f"✅ Installed workflow: {resource_id}")
        else:
            typer.echo("❌ Source path required for workflow installation")
            raise typer.Exit(1)
    elif resource_type == "blueprint":
        if source_path:
            blueprint = Blueprint.from_yaml(source_path)
            registry.register_blueprint(blueprint)
            typer.echo(f"✅ Installed blueprint: {resource_id}")
        else:
            typer.echo("❌ Source path required for blueprint installation")
            raise typer.Exit(1)
    else:
        typer.echo(f"❌ Unknown resource type: {resource_type}")
        raise typer.Exit(1)


@app.command()
def uninstall(
    resource_type: str = typer.Argument(
        ..., help="Resource type: agent, tool, workflow, blueprint"
    ),
    resource_id: str = typer.Argument(..., help="Resource ID"),
):
    """Uninstall a resource from registry."""
    registry = LocalRegistry()

    if resource_type == "agent":
        if registry.delete_agent(resource_id):
            typer.echo(f"✅ Uninstalled agent: {resource_id}")
        else:
            typer.echo(f"❌ Agent not found: {resource_id}")
            raise typer.Exit(1)
    elif resource_type == "tool":
        tool_file = registry.base_path / "tools" / f"{resource_id}.json"
        if tool_file.exists():
            tool_file.unlink()
            typer.echo(f"✅ Uninstalled tool: {resource_id}")
        else:
            typer.echo(f"❌ Tool not found: {resource_id}")
            raise typer.Exit(1)
    elif resource_type == "workflow":
        workflow_file = registry.base_path / "workflows" / f"{resource_id}.json"
        if workflow_file.exists():
            workflow_file.unlink()
            typer.echo(f"✅ Uninstalled workflow: {resource_id}")
        else:
            typer.echo(f"❌ Workflow not found: {resource_id}")
            raise typer.Exit(1)
    elif resource_type == "blueprint":
        blueprint_dir = registry.base_path / "blueprints" / resource_id
        if blueprint_dir.exists():
            import shutil

            shutil.rmtree(blueprint_dir)
            typer.echo(f"✅ Uninstalled blueprint: {resource_id}")
        else:
            typer.echo(f"❌ Blueprint not found: {resource_id}")
            raise typer.Exit(1)
    else:
        typer.echo(f"❌ Unknown resource type: {resource_type}")
        raise typer.Exit(1)


@app.command()
def update(
    resource_type: str = typer.Argument(
        ..., help="Resource type: agent, tool, workflow, blueprint"
    ),
    resource_id: str = typer.Argument(..., help="Resource ID"),
    source_path: str = typer.Option(..., "--source", "-s", help="Source path for update"),
):
    """Update a resource in registry."""
    registry = LocalRegistry()

    if resource_type == "agent":
        import json

        agent_data = json.loads(Path(source_path).read_text())
        agent = Agent.from_dict(agent_data)
        registry.register_agent(agent)
        typer.echo(f"✅ Updated agent: {resource_id}")
    elif resource_type == "tool":
        import json

        tool_data = json.loads(Path(source_path).read_text())

        def placeholder(**kwargs):
            raise NotImplementedError("Tool implementation not available")

        tool = Tool(
            id=tool_data.get("id", resource_id),
            name=tool_data.get("name", resource_id),
            description=tool_data.get("description", ""),
            implementation=placeholder,
        )
        registry.register_tool(tool)
        typer.echo(f"✅ Updated tool: {resource_id}")
    elif resource_type == "workflow":
        import json

        json.loads(Path(source_path).read_text())
        workflow = registry.get_workflow(resource_id)
        if workflow:
            registry.register_workflow(workflow)
            typer.echo(f"✅ Updated workflow: {resource_id}")
        else:
            typer.echo("❌ Workflow reconstruction required")
            raise typer.Exit(1)
    elif resource_type == "blueprint":
        blueprint = Blueprint.from_yaml(source_path)
        registry.register_blueprint(blueprint)
        typer.echo(f"✅ Updated blueprint: {resource_id}")
    else:
        typer.echo(f"❌ Unknown resource type: {resource_type}")
        raise typer.Exit(1)
