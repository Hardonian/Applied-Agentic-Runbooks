"""Agent CLI commands."""


import typer

from agent_factory.agents.agent import Agent
from agent_factory.registry.local_registry import LocalRegistry

app = typer.Typer(name="agent", help="Manage agents")


@app.command()
def create(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    name: str = typer.Option(..., "--name", "-n", help="Agent name"),
    instructions: str = typer.Option(..., "--instructions", "-i", help="Agent instructions"),
    model: str = typer.Option("gpt-4o", "--model", "-m", help="LLM model"),
):
    """Create a new agent."""
    agent = Agent(
        id=agent_id,
        name=name,
        instructions=instructions,
        model=model,
    )
    
    registry = LocalRegistry()
    registry.register_agent(agent)
    
    typer.echo(f"✅ Created agent: {agent_id}")


@app.command()
def list():
    """List all agents."""
    registry = LocalRegistry()
    agents = registry.list_agents()
    
    if not agents:
        typer.echo("No agents found.")
        return
    
    typer.echo("Agents:")
    for agent_id in agents:
        agent = registry.get_agent(agent_id)
        if agent:
            typer.echo(f"  - {agent_id}: {agent.name}")


@app.command()
def run(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    input_text: str = typer.Option(..., "--input", "-i", help="Input text"),
    session_id: str | None = typer.Option(None, "--session", "-s", help="Session ID"),
):
    """Run an agent."""
    registry = LocalRegistry()
    agent = registry.get_agent(agent_id)
    
    if not agent:
        typer.echo(f"❌ Agent not found: {agent_id}")
        raise typer.Exit(1)
    
    result = agent.run(input_text, session_id=session_id)
    
    if result.status.value == "error":
        typer.echo(f"❌ Error: {result.error}")
        raise typer.Exit(1)
    
    typer.echo(result.output)


@app.command()
def delete(
    agent_id: str = typer.Argument(..., help="Agent ID"),
):
    """Delete an agent."""
    registry = LocalRegistry()
    
    if registry.delete_agent(agent_id):
        typer.echo(f"✅ Deleted agent: {agent_id}")
    else:
        typer.echo(f"❌ Agent not found: {agent_id}")
        raise typer.Exit(1)
