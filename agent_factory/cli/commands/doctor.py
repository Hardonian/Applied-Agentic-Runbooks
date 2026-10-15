"""
CLI command for system diagnostics and health checks.
"""

import sys
from pathlib import Path

import typer

app = typer.Typer(name="doctor", help="System diagnostics and health checks")


def check_python_version() -> tuple[bool, str]:
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)"


def check_dependencies() -> list[tuple[str, bool, str]]:
    """Check required dependencies."""
    results = []
    required = [
        ("openai", "OpenAI SDK"),
        ("anthropic", "Anthropic SDK"),
        ("fastapi", "FastAPI"),
        ("typer", "Typer CLI"),
        ("pydantic", "Pydantic"),
        ("yaml", "PyYAML"),
        ("dotenv", "python-dotenv"),
        ("httpx", "HTTPX"),
        ("sqlalchemy", "SQLAlchemy"),
        ("redis", "Redis"),
    ]
    
    for module, name in required:
        try:
            __import__(module)
            results.append((name, True, "Installed"))
        except ImportError:
            results.append((name, False, "Not installed"))
    
    return results


def check_env_vars() -> list[tuple[str, bool, str]]:
    """Check environment variables."""
    import os
    results = []
    
    vars_to_check = [
        ("OPENAI_API_KEY", False),  # Optional but recommended
        ("ANTHROPIC_API_KEY", False),  # Optional
        ("AGENT_FACTORY_REGISTRY_PATH", False),  # Optional
    ]
    
    for var, required in vars_to_check:
        value = os.getenv(var)
        if value:
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            results.append((var, True, f"Set ({masked})"))
        elif required:
            results.append((var, False, "Required but not set"))
        else:
            results.append((var, False, "Not set (optional)"))
    
    return results


def check_registry() -> tuple[bool, str]:
    """Check registry directory."""
    try:
        from agent_factory.utils.config import Config
        config = Config()
        registry_path = Path(config.registry_path).expanduser()
        
        if registry_path.exists():
            return True, f"Registry exists: {registry_path}"
        else:
            registry_path.mkdir(parents=True, exist_ok=True)
            return True, f"Registry created: {registry_path}"
    except Exception as e:
        return False, f"Registry check failed: {e}"


def check_blueprints() -> tuple[bool, str, int]:
    """Check installed blueprints."""
    try:
        from agent_factory.registry.local_registry import LocalRegistry
        registry = LocalRegistry()
        blueprints = registry.list_blueprints()
        count = len(blueprints)
        if count > 0:
            return True, f"Found {count} installed blueprint(s)", count
        else:
            return True, "No blueprints installed", 0
    except Exception as e:
        return False, f"Blueprint check failed: {e}", 0


@app.command()
def run(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Run system diagnostics."""
    typer.echo("🔍 Agent Factory System Diagnostics\n")
    
    issues = []
    warnings = []
    
    # Python version
    ok, msg = check_python_version()
    status = "✅" if ok else "❌"
    typer.echo(f"{status} {msg}")
    if not ok:
        issues.append("Python version")
    
    # Dependencies
    typer.echo("\n📦 Dependencies:")
    deps = check_dependencies()
    for name, ok, msg in deps:
        status = "✅" if ok else "❌"
        typer.echo(f"  {status} {name}: {msg}")
        if not ok:
            issues.append(f"Dependency: {name}")
    
    # Environment variables
    typer.echo("\n🔐 Environment Variables:")
    env_vars = check_env_vars()
    for var, ok, msg in env_vars:
        status = "✅" if ok else "⚠️"
        typer.echo(f"  {status} {var}: {msg}")
        if not ok and "Required" in msg:
            issues.append(f"Environment variable: {var}")
        elif not ok:
            warnings.append(f"Environment variable: {var} not set")
    
    # Registry
    typer.echo("\n📁 Registry:")
    ok, msg = check_registry()
    status = "✅" if ok else "❌"
    typer.echo(f"  {status} {msg}")
    if not ok:
        issues.append("Registry")
    
    # Blueprints
    typer.echo("\n📦 Blueprints:")
    ok, msg, count = check_blueprints()
    status = "✅" if ok else "❌"
    typer.echo(f"  {status} {msg}")
    if not ok:
        issues.append("Blueprints")
    elif count == 0:
        warnings.append("No blueprints installed")
    
    # Summary
    typer.echo("\n" + "="*50)
    if issues:
        typer.echo(f"❌ Found {len(issues)} issue(s):")
        for issue in issues:
            typer.echo(f"   - {issue}")
        typer.echo("\n💡 Run 'agent-factory doctor --help' for troubleshooting")
        raise typer.Exit(1)
    elif warnings:
        typer.echo(f"⚠️  Found {len(warnings)} warning(s):")
        for warning in warnings:
            typer.echo(f"   - {warning}")
        typer.echo("\n✅ System is functional but some optional features may be unavailable")
    else:
        typer.echo("✅ All checks passed! System is ready.")
    
    if verbose:
        typer.echo("\n📊 System Information:")
        import platform
        typer.echo(f"  Platform: {platform.system()} {platform.release()}")
        typer.echo(f"  Architecture: {platform.machine()}")
        try:
            from agent_factory import __version__
            typer.echo(f"  Agent Factory: {__version__}")
        except Exception:
            pass
