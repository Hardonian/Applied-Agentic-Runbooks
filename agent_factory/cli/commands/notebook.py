"""
CLI commands for notebook conversion.
"""

import typer

from agent_factory.notebook_converter import NotebookConverter

app = typer.Typer(name="notebook", help="Notebook conversion commands")


@app.command()
def convert(
    notebook_path: str = typer.Argument(..., help="Path to .ipynb file"),
    agent_name: str = typer.Option(None, "--agent-name", "-n", help="Name for extracted agent"),
    output_dir: str = typer.Option(
        "./agent_factory", "--output-dir", "-o", help="Output directory"
    ),
    create_blueprint: bool = typer.Option(
        False, "--create-blueprint", help="Create blueprint.yaml"
    ),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode"),
):
    """Convert a Jupyter notebook to agents, tools, and workflows."""
    converter = NotebookConverter(output_dir=output_dir)

    try:
        result = converter.convert(
            notebook_path=notebook_path,
            agent_name=agent_name,
            create_blueprint=create_blueprint,
            interactive=interactive,
        )

        typer.echo("✅ Conversion complete!")
        typer.echo(f"   Agents created: {len(result.agents_created)}")
        typer.echo(f"   Tools created: {len(result.tools_created)}")
        typer.echo(f"   Workflows created: {len(result.workflows_created)}")

        if result.blueprint_created:
            typer.echo(f"   Blueprint created: {result.blueprint_created}")

        if result.errors:
            typer.echo("\n⚠️  Errors:")
            for error in result.errors:
                typer.echo(f"   - {error}")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1) from e
