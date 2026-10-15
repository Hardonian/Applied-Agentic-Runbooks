"""Marketplace CLI commands."""


import typer

from agent_factory.marketplace import get_blueprint_details, publish_blueprint, search_blueprints
from agent_factory.registry.local_registry import LocalRegistry

app = typer.Typer()
registry = LocalRegistry()


@app.command()
def publish(
    blueprint_id: str,
    public: bool = typer.Option(True, "--public/--private", help="Make blueprint public"),
    pricing: str = typer.Option("free", help="Pricing model: free, one-time, subscription"),
    price: float = typer.Option(0.0, help="Price in USD"),
):
    """Publish blueprint to marketplace."""
    blueprint = registry.get_blueprint(blueprint_id)
    
    if not blueprint:
        typer.echo(f"Blueprint {blueprint_id} not found", err=True)
        raise typer.Exit(1)
    
    try:
        result = publish_blueprint(
            blueprint=blueprint,
            publisher_id="cli-user",  # In production, get from auth
            is_public=public,
            pricing_model=pricing,
            price=price
        )
        typer.echo(f"Blueprint published: {result['id']}")
    except Exception as e:
        typer.echo(f"Failed to publish blueprint: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def search(
    query: str | None = typer.Option(None, "--query", "-q", help="Search query"),
    category: str | None = typer.Option(None, "--category", "-c", help="Category filter"),
    limit: int = typer.Option(20, "--limit", "-l", help="Results limit"),
):
    """Search blueprints in marketplace."""
    results = search_blueprints(
        query=query,
        category=category,
        limit=limit
    )
    
    typer.echo(f"Found {results['total']} blueprints:")
    for bp in results["blueprints"]:
        typer.echo(f"  - {bp['name']} ({bp['id']}) - Rating: {bp['rating']:.1f}")


@app.command()
def details(blueprint_id: str):
    """Get blueprint details from marketplace."""
    details = get_blueprint_details(blueprint_id)
    
    if not details:
        typer.echo(f"Blueprint {blueprint_id} not found", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Name: {details['name']}")
    typer.echo(f"Description: {details['description']}")
    typer.echo(f"Version: {details['version']}")
    typer.echo(f"Pricing: {details['pricing_model']} - ${details['price']:.2f}")
    typer.echo(f"Rating: {details['rating']:.1f} ({details['reviews_count']} reviews)")
    typer.echo(f"Downloads: {details['downloads']}")


@app.command()
def install(
    blueprint_id: str = typer.Argument(..., help="Blueprint ID"),
    target_path: str = typer.Option(".", "--path", "-p", help="Installation path"),
):
    """Install a blueprint from marketplace."""
    from agent_factory.registry.remote_registry import RemoteRegistry
    
    registry = RemoteRegistry()
    
    try:
        success = registry.install_blueprint(blueprint_id, target_path)
        if success:
            typer.echo(f"✅ Installed blueprint from marketplace: {blueprint_id}")
        else:
            typer.echo(f"❌ Installation failed: {blueprint_id}")
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(1)


@app.command()
def unpublish(
    blueprint_id: str = typer.Argument(..., help="Blueprint ID"),
):
    """Unpublish a blueprint from marketplace."""
    from agent_factory.marketplace.publishing import unpublish_blueprint
    
    try:
        result = unpublish_blueprint(
            blueprint_id=blueprint_id,
            publisher_id="cli-user"  # In production, get from auth
        )
        typer.echo(f"✅ Unpublished blueprint: {result['id']}")
    except Exception as e:
        typer.echo(f"❌ Unpublishing failed: {e}")
        raise typer.Exit(1)


@app.command()
def my_blueprints():
    """List my published blueprints."""
    # In production, would fetch from database filtered by user
    typer.echo("My Published Blueprints:")
    typer.echo("💡 This feature requires authentication integration")
    typer.echo("   Use 'agent-factory blueprint list' to see local blueprints")
