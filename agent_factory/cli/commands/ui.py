"""
CLI commands for UI generation.
"""

import subprocess  # nosec B404 -- subprocess is required to launch the Streamlit UI in a child process
import sys
from pathlib import Path

import typer

app = typer.Typer(name="ui", help="UI generation commands")


@app.command()
def generate(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    output: str = typer.Option("./ui", "--output", "-o", help="Output directory"),
    template: str = typer.Option("react", "--template", "-t", help="Template type (react or html)"),
):
    """Generate UI for an agent."""
    try:
        from agent_factory.ui import generate_ui

        generate_ui(agent_id, output, template)
        typer.echo(f"✅ UI generated at: {output}")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def demo(
    port: int = typer.Option(8501, "--port", "-p", help="Port to run demo on"),
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
):
    """Launch the Streamlit demo UI."""
    try:
        import streamlit  # noqa: F401 -- availability check before subprocess launch
    except ImportError:
        typer.echo("❌ Streamlit not installed. Install with: pip install streamlit")
        typer.echo("   Or install demo dependencies: pip install 'agent-factory[demo]'")
        raise typer.Exit(1)

    demo_path = Path(__file__).parent.parent.parent / "demo" / "app.py"

    if not demo_path.exists():
        typer.echo(f"❌ Demo UI not found at: {demo_path}")
        raise typer.Exit(1)

    typer.echo(f"🚀 Starting Agent Factory Demo UI on http://{host}:{port}")
    typer.echo("   Press Ctrl+C to stop")

    try:
        subprocess.run(
            [  # nosec B603 -- argv is a fixed literal list (sys.executable -m streamlit); shell never used, so there is no shell-parsing surface
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(demo_path),
                "--server.port",
                str(port),
                "--server.address",
                host,
            ]
        )
    except KeyboardInterrupt:
        typer.echo("\n👋 Demo UI stopped")
