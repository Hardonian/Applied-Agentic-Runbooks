"""Tool CLI commands."""

import json
from pathlib import Path

import typer

from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.tools.base import Tool

app = typer.Typer(name="tool", help="Manage tools")


@app.command()
def list():
    """List all tools."""
    registry = LocalRegistry()
    tools = registry.list_tools()

    if not tools:
        typer.echo("No tools found.")
        return

    typer.echo("Tools:")
    for tool_id in tools:
        tool = registry.get_tool(tool_id)
        if tool:
            typer.echo(f"  - {tool_id}: {tool.name}")
        else:
            typer.echo(f"  - {tool_id}")


@app.command()
def create(
    tool_id: str = typer.Argument(..., help="Tool ID"),
    name: str = typer.Option(..., "--name", "-n", help="Tool name"),
    description: str = typer.Option(..., "--description", "-d", help="Tool description"),
    implementation_file: str | None = typer.Option(
        None, "--impl", "-i", help="Path to implementation file"
    ),
):
    """Create a new tool."""
    registry = LocalRegistry()

    # Check if tool exists
    if registry.get_tool(tool_id):
        typer.echo(f"❌ Tool {tool_id} already exists")
        raise typer.Exit(1)

    # Create placeholder implementation
    def placeholder_implementation(**kwargs):
        raise NotImplementedError(
            f"Tool {tool_id} implementation not available. "
            "Please provide implementation function via --impl flag."
        )

    tool = Tool(
        id=tool_id,
        name=name,
        description=description,
        implementation=placeholder_implementation,
    )

    registry.register_tool(tool)
    typer.echo(f"✅ Created tool: {tool_id}")
    typer.echo("💡 Note: Tool needs implementation function. Use 'tool update' to add it.")


@app.command()
def register(
    tool_id: str = typer.Argument(..., help="Tool ID"),
    tool_path: str = typer.Option(..., "--path", "-p", help="Path to tool JSON file"),
):
    """Register a tool from JSON file."""
    tool_file = Path(tool_path)

    if not tool_file.exists():
        typer.echo(f"❌ Tool file not found: {tool_path}")
        raise typer.Exit(1)

    # Load tool data
    with open(tool_file) as f:
        tool_data = json.load(f)

    registry = LocalRegistry()

    # Create placeholder tool (implementation cannot be fully reconstructed)
    def placeholder_implementation(**kwargs):
        raise NotImplementedError(
            f"Tool {tool_id} implementation not available. "
            "Please re-register with implementation function."
        )

    tool = Tool(
        id=tool_data.get("id", tool_id),
        name=tool_data.get("name", tool_id),
        description=tool_data.get("description", ""),
        implementation=placeholder_implementation,
    )

    registry.register_tool(tool)
    typer.echo(f"✅ Registered tool: {tool_id}")
    typer.echo("💡 Note: Implementation function needs to be provided separately.")


@app.command()
def update(
    tool_id: str = typer.Argument(..., help="Tool ID"),
    name: str | None = typer.Option(None, "--name", "-n", help="Tool name"),
    description: str | None = typer.Option(None, "--description", "-d", help="Tool description"),
):
    """Update a tool."""
    registry = LocalRegistry()
    tool = registry.get_tool(tool_id)

    if not tool:
        typer.echo(f"❌ Tool not found: {tool_id}")
        raise typer.Exit(1)

    if name:
        tool.name = name
    if description:
        tool.description = description

    registry.register_tool(tool)
    typer.echo(f"✅ Updated tool: {tool_id}")


@app.command()
def delete(
    tool_id: str = typer.Argument(..., help="Tool ID"),
):
    """Delete a tool."""
    registry = LocalRegistry()
    tool_file = registry.base_path / "tools" / f"{tool_id}.json"

    if not tool_file.exists():
        typer.echo(f"❌ Tool not found: {tool_id}")
        raise typer.Exit(1)

    tool_file.unlink()
    typer.echo(f"✅ Deleted tool: {tool_id}")


@app.command()
def test(
    tool_id: str = typer.Argument(..., help="Tool ID"),
    params: str = typer.Option(..., "--params", "-p", help="JSON parameters"),
):
    """Test a tool with given parameters."""
    registry = LocalRegistry()
    tool = registry.get_tool(tool_id)

    if not tool:
        typer.echo(f"❌ Tool not found: {tool_id}")
        raise typer.Exit(1)

    try:
        params_dict = json.loads(params)
        result = tool.execute(**params_dict)
        typer.echo(f"✅ Result: {result}")
    except NotImplementedError as e:
        typer.echo(f"❌ Error: {e}")
        typer.echo(
            "💡 Tool implementation not available. Please register with implementation function."
        )
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(1) from e


@app.command()
def schema(
    tool_id: str = typer.Argument(..., help="Tool ID"),
):
    """Get tool schema."""
    registry = LocalRegistry()
    tool = registry.get_tool(tool_id)

    if not tool:
        typer.echo(f"❌ Tool not found: {tool_id}")
        raise typer.Exit(1)

    schema = tool.get_schema()
    typer.echo(json.dumps(schema, indent=2))
