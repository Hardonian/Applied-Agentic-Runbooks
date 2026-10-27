"""Blueprint CLI commands."""

import typer

from agent_factory.blueprints.model import Blueprint
from agent_factory.marketplace import publish_blueprint
from agent_factory.registry.local_registry import LocalRegistry

app = typer.Typer(name="blueprint", help="Manage blueprints")


@app.command()
def install(
    blueprint_id: str = typer.Argument(..., help="Blueprint ID"),
    target_path: str = typer.Option(".", "--path", "-p", help="Installation path"),
    version: str | None = typer.Option(
        None, "--version", "-v", help="Blueprint version constraint (e.g., '1.0.0', '>=1.0.0')"
    ),
    from_marketplace: bool = typer.Option(
        False, "--marketplace", "-m", help="Install from marketplace index"
    ),
    verify_hash: bool = typer.Option(
        True, "--verify-hash/--no-verify-hash", help="Verify blueprint hash"
    ),
):
    """Install a blueprint."""

    registry = LocalRegistry()

    # Try marketplace first if requested
    if from_marketplace:
        try:
            import json
            from pathlib import Path

            import httpx

            index_path = Path("blueprints_index.json")
            if not index_path.exists():
                # Try to download from remote
                typer.echo("📥 Downloading marketplace index...")
                try:
                    response = httpx.get(
                        "https://raw.githubusercontent.com/agentfactory/platform/main/blueprints_index.json",
                        timeout=10.0,
                    )
                    if response.status_code == 200:
                        index_data = response.json()
                    else:
                        typer.echo("⚠️  Could not download marketplace index, using local registry")
                        from_marketplace = False
                except Exception as e:
                    typer.echo(f"⚠️  Could not download marketplace index: {e}")
                    from_marketplace = False

            if from_marketplace and index_path.exists():
                with open(index_path, "r") as f:
                    index_data = json.load(f)

                blueprint_entry = next(
                    (bp for bp in index_data.get("blueprints", []) if bp["id"] == blueprint_id),
                    None,
                )

                if blueprint_entry:
                    # Check version compatibility
                    if version:
                        bp_version = blueprint_entry.get("version", "0.0.0")
                        if not _check_version_constraint(bp_version, version):
                            typer.echo(
                                f"❌ Version mismatch: blueprint is {bp_version}, requested {version}"
                            )
                            raise typer.Exit(1)

                    # Check compatibility
                    compat = blueprint_entry.get("compatibility", {})
                    af_version = compat.get("agent_factory_version", ">=0.1.0")
                    from agent_factory import __version__

                    if not _check_version_constraint(__version__, af_version):
                        typer.echo(
                            f"⚠️  Warning: Agent Factory version {__version__} may not be compatible with blueprint requirement {af_version}"
                        )

                    # Download blueprint
                    download_url = blueprint_entry.get("download_url")
                    if download_url:
                        typer.echo("📥 Downloading blueprint from marketplace...")
                        try:
                            response = httpx.get(download_url, timeout=30.0)
                            if response.status_code == 200:
                                # Verify hash if requested
                                if verify_hash:
                                    import hashlib

                                    content_hash = (
                                        f"sha256:{hashlib.sha256(response.content).hexdigest()}"
                                    )
                                    expected_hash = blueprint_entry.get("hash", "")
                                    if expected_hash and content_hash != expected_hash:
                                        typer.echo("❌ Hash verification failed!")
                                        typer.echo(f"   Expected: {expected_hash}")
                                        typer.echo(f"   Got: {content_hash}")
                                        raise typer.Exit(1)

                                # Save and load blueprint
                                from tempfile import NamedTemporaryFile

                                with NamedTemporaryFile(
                                    mode="w", suffix=".yaml", delete=False
                                ) as f:
                                    f.write(response.text)
                                    temp_path = f.name

                                mp_blueprint = Blueprint.from_yaml(temp_path)
                                import os

                                os.unlink(temp_path)

                                registry.register_blueprint(mp_blueprint)
                                typer.echo(
                                    f"✅ Installed blueprint from marketplace: {blueprint_id} v{blueprint_entry.get('version')}"
                                )

                                if mp_blueprint.install(target_path):
                                    typer.echo(f"✅ Installed blueprint files to: {target_path}")
                                return
                        except Exception as e:
                            typer.echo(f"⚠️  Marketplace download failed: {e}")
                            typer.echo("   Falling back to local registry...")

        except Exception as e:
            typer.echo(f"⚠️  Marketplace error: {e}")
            typer.echo("   Falling back to local registry...")

    # Fall back to local registry
    blueprint = registry.get_blueprint(blueprint_id)

    if not blueprint:
        typer.echo(f"❌ Blueprint not found: {blueprint_id}")
        typer.echo("💡 Try: agent-factory blueprint search <query>")
        typer.echo(
            "💡 Or install from marketplace: agent-factory blueprint install <id> --marketplace"
        )
        raise typer.Exit(1)

    # Check version if specified
    if version and hasattr(blueprint, "version"):
        if not _check_version_constraint(blueprint.version, version):
            typer.echo(
                f"❌ Version mismatch: blueprint is {blueprint.version}, requested {version}"
            )
            raise typer.Exit(1)

    if blueprint.install(target_path):
        typer.echo(f"✅ Installed blueprint: {blueprint_id}")
    else:
        typer.echo(f"❌ Installation failed: {blueprint_id}")
        raise typer.Exit(1)


def _check_version_constraint(version: str, constraint: str) -> bool:
    """Check if version satisfies constraint."""
    try:
        from packaging import version as pkg_version
        from packaging.specifiers import SpecifierSet

        if constraint.startswith((">=", "<=", "==", "!=", "~=", ">")):
            spec = SpecifierSet(constraint)
            return spec.contains(version)
        else:
            # Exact match
            return pkg_version.parse(version) == pkg_version.parse(constraint)
    except Exception:
        # If parsing fails, do simple string comparison
        return version == constraint


@app.command("list")
def list_blueprints():
    """List installed blueprints."""
    registry = LocalRegistry()
    blueprints = registry.list_blueprints()

    if not blueprints:
        typer.echo("No blueprints installed.")
        return

    typer.echo("Blueprints:")
    for blueprint_id in blueprints:
        blueprint = registry.get_blueprint(blueprint_id)
        if blueprint:
            typer.echo(f"  - {blueprint_id}: {blueprint.name} (v{blueprint.version})")


@app.command()
def create(
    blueprint_path: str = typer.Argument(..., help="Path to blueprint.yaml"),
):
    """Create a blueprint from YAML file."""
    blueprint = Blueprint.from_yaml(blueprint_path)

    registry = LocalRegistry()
    registry.register_blueprint(blueprint)

    typer.echo(f"✅ Created blueprint: {blueprint.id}")


@app.command()
def update(
    blueprint_id: str = typer.Argument(..., help="Blueprint ID"),
    name: str | None = typer.Option(None, "--name", "-n", help="Blueprint name"),
    description: str | None = typer.Option(
        None, "--description", "-d", help="Blueprint description"
    ),
    version: str | None = typer.Option(None, "--version", "-v", help="Blueprint version"),
):
    """Update a blueprint."""
    registry = LocalRegistry()
    blueprint = registry.get_blueprint(blueprint_id)

    if not blueprint:
        typer.echo(f"❌ Blueprint not found: {blueprint_id}")
        raise typer.Exit(1)

    if name:
        blueprint.name = name
    if description:
        blueprint.description = description
    if version:
        blueprint.version = version

    registry.register_blueprint(blueprint)
    typer.echo(f"✅ Updated blueprint: {blueprint_id}")


@app.command()
def delete(
    blueprint_id: str = typer.Argument(..., help="Blueprint ID"),
):
    """Delete a blueprint."""
    registry = LocalRegistry()
    blueprint_dir = registry.base_path / "blueprints" / blueprint_id

    if not blueprint_dir.exists():
        typer.echo(f"❌ Blueprint not found: {blueprint_id}")
        raise typer.Exit(1)

    import shutil

    shutil.rmtree(blueprint_dir)
    typer.echo(f"✅ Deleted blueprint: {blueprint_id}")


@app.command()
def validate(
    blueprint_path: str = typer.Argument(..., help="Path to blueprint.yaml"),
):
    """Validate a blueprint."""
    try:
        blueprint = Blueprint.from_yaml(blueprint_path)
        typer.echo(f"✅ Blueprint is valid: {blueprint.id}")
        typer.echo(f"   Name: {blueprint.name}")
        typer.echo(f"   Version: {blueprint.version}")
        typer.echo(f"   Agents: {len(blueprint.agents)}")
        typer.echo(f"   Tools: {len(blueprint.tools)}")
        typer.echo(f"   Workflows: {len(blueprint.workflows)}")
    except Exception as e:
        typer.echo(f"❌ Blueprint validation failed: {e}")
        raise typer.Exit(1)


@app.command()
def test(
    blueprint_id: str = typer.Argument(..., help="Blueprint ID"),
    test_input: str | None = typer.Option(None, "--input", "-i", help="Test input"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Test a blueprint by running it with sample input."""
    registry = LocalRegistry()
    blueprint = registry.get_blueprint(blueprint_id)

    if not blueprint:
        typer.echo(f"❌ Blueprint not found: {blueprint_id}")
        raise typer.Exit(1)

    typer.echo(f"🧪 Testing blueprint: {blueprint_id}\n")

    # Use provided input or default
    input_text = test_input or "Hello, this is a test"

    typer.echo(f"📥 Input: {input_text}\n")

    try:
        # Try to run the first agent if available
        if hasattr(blueprint, "agents") and blueprint.agents:
            agent_id = (
                blueprint.agents[0]
                if isinstance(blueprint.agents, list)
                else list(blueprint.agents.keys())[0]
            )

            from agent_factory.agents.agent import Agent

            reg = LocalRegistry()
            agent_config = reg.get_agent(agent_id)

            if agent_config:
                agent = Agent(
                    id=agent_id,
                    name=getattr(agent_config, "name", agent_id),
                    instructions=getattr(agent_config, "instructions", ""),
                    tools=getattr(agent_config, "tools", []),
                )

                typer.echo("⏳ Running agent...")
                result = agent.run(input_text)

                typer.echo("\n✅ Test completed successfully!")
                typer.echo(
                    f"📤 Output: {result.output if hasattr(result, 'output') else str(result)}"
                )

                if verbose:
                    typer.echo("\n📊 Details:")
                    typer.echo(f"   Agent ID: {agent_id}")
                    typer.echo(f"   Blueprint: {blueprint_id}")
            else:
                typer.echo("⚠️  Agent not found in registry, skipping execution test")
                typer.echo("✅ Blueprint structure is valid")
        else:
            typer.echo("⚠️  No agents found in blueprint, skipping execution test")
            typer.echo("✅ Blueprint structure is valid")

    except Exception as e:
        typer.echo(f"❌ Test failed: {e}")
        if verbose:
            import traceback

            typer.echo(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def publish(
    blueprint_id: str = typer.Argument(..., help="Blueprint ID"),
    public: bool = typer.Option(True, "--public/--private", help="Make blueprint public"),
    pricing: str = typer.Option("free", help="Pricing model: free, one-time, subscription"),
    price: float = typer.Option(0.0, help="Price in USD"),
):
    """Publish a blueprint to marketplace."""
    registry = LocalRegistry()
    blueprint = registry.get_blueprint(blueprint_id)

    if not blueprint:
        typer.echo(f"❌ Blueprint not found: {blueprint_id}")
        raise typer.Exit(1)

    try:
        result = publish_blueprint(
            blueprint=blueprint,
            publisher_id="cli-user",  # In production, get from auth
            is_public=public,
            pricing_model=pricing,
            price=price,
        )
        typer.echo(f"✅ Published blueprint: {result['id']}")
        typer.echo(f"   Status: {result['status']}")
    except Exception as e:
        typer.echo(f"❌ Publishing failed: {e}")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
):
    """Search for blueprints."""
    registry = LocalRegistry()
    results = registry.search(query, category="blueprint")

    blueprints = results.get("blueprints", [])

    if not blueprints:
        typer.echo(f"No blueprints found for: {query}")
        return

    typer.echo(f"Found {len(blueprints)} blueprints:")
    for blueprint_id in blueprints:
        blueprint = registry.get_blueprint(blueprint_id)
        if blueprint:
            typer.echo(f"  - {blueprint_id}: {blueprint.name}")
