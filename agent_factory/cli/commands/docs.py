"""
CLI commands for documentation generation.
"""

from pathlib import Path

import typer

app = typer.Typer(name="docs", help="Documentation generation")


@app.command()
def generate(
    output_dir: str = typer.Option("./docs", "--output", "-o", help="Output directory"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format (markdown, html)"),
    include_examples: bool = typer.Option(True, "--examples/--no-examples", help="Include examples"),
):
    """Generate documentation from code and blueprints."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    typer.echo("📚 Generating documentation...\n")
    
    # Generate API documentation
    typer.echo("📖 Generating API documentation...")
    try:
        from agent_factory import __version__
        api_doc = f"""# Agent Factory API Reference

Version: {__version__}

## Core Classes

### Agent

The main agent class for creating and running AI agents.

```python
from agent_factory import Agent

agent = Agent(
    id="my-agent",
    name="My Agent",
    instructions="You are a helpful assistant.",
    tools=[]
)

result = agent.run("Hello!")
```

### Tool

Base class for creating custom tools.

```python
from agent_factory import Tool, function_tool

@function_tool
def my_tool(input: str) -> str:
    \"\"\"Tool description.\"\"\"
    return f"Processed: {input}"
```

### Blueprint

Blueprint for packaging agents, tools, and workflows.

```python
from agent_factory import Blueprint

blueprint = Blueprint.from_yaml("blueprint.yaml")
```

### Workflow

Workflow for orchestrating multiple agents.

```python
from agent_factory import Workflow

workflow = Workflow.from_yaml("workflow.yaml")
```

## CLI Commands

### agent-factory doctor

Run system diagnostics.

```bash
agent-factory doctor
```

### agent-factory config check

Check configuration.

```bash
agent-factory config check
```

### agent-factory blueprint install

Install a blueprint.

```bash
agent-factory blueprint install research-assistant
```

### agent-factory blueprint test

Test a blueprint.

```bash
agent-factory blueprint test research-assistant
```

## Examples

See the `examples/` directory for complete examples.

"""
        
        (output_path / "API_REFERENCE.md").write_text(api_doc)
        typer.echo("   ✅ API reference generated")
    except Exception as e:
        typer.echo(f"   ⚠️  API reference generation failed: {e}")
    
    # Generate blueprint documentation
    typer.echo("\n📦 Generating blueprint documentation...")
    try:
        from agent_factory.registry.local_registry import LocalRegistry
        registry = LocalRegistry()
        blueprints = registry.list_blueprints()
        
        blueprint_doc = "# Available Blueprints\n\n"
        
        for bp_id in blueprints:
            blueprint = registry.get_blueprint(bp_id)
            if blueprint:
                blueprint_doc += f"## {blueprint.name}\n\n"
                blueprint_doc += f"**ID:** `{blueprint.id}`\n\n"
                if hasattr(blueprint, 'description'):
                    blueprint_doc += f"{blueprint.description}\n\n"
                if hasattr(blueprint, 'version'):
                    blueprint_doc += f"**Version:** {blueprint.version}\n\n"
                blueprint_doc += f"**Install:** `agent-factory blueprint install {blueprint.id}`\n\n"
                blueprint_doc += "---\n\n"
        
        (output_path / "BLUEPRINTS.md").write_text(blueprint_doc)
        typer.echo(f"   ✅ Blueprint documentation generated ({len(blueprints)} blueprints)")
    except Exception as e:
        typer.echo(f"   ⚠️  Blueprint documentation generation failed: {e}")
    
    # Generate quick start guide
    typer.echo("\n🚀 Generating quick start guide...")
    try:
        quickstart = """# Quick Start Guide

## Installation

```bash
pip install agent-factory
```

## Your First Agent

```python
from agent_factory import Agent

agent = Agent(
    id="greeting-agent",
    name="Greeting Agent",
    instructions="You are a friendly assistant that greets users.",
    tools=[]
)

result = agent.run("Hello!")
print(result.output)
```

## Using Tools

```python
from agent_factory import Agent, function_tool

@function_tool
def calculate(expression: str) -> float:
    \"\"\"Calculate a mathematical expression.\"\"\"
    return eval(expression)

agent = Agent(
    id="calculator-agent",
    name="Calculator Agent",
    instructions="You are a calculator assistant.",
    tools=[calculate]
)

result = agent.run("What is 15 * 23?")
print(result.output)
```

## Installing Blueprints

```bash
# Install from marketplace
agent-factory blueprint install research-assistant --marketplace

# List installed blueprints
agent-factory blueprint list
```

## Running the Demo UI

```bash
agent-factory ui demo
```

## Next Steps

- Read the [User Guide](USER_GUIDE.md)
- Explore [Examples](../examples/)
- Check out [Blueprints](BLUEPRINTS.md)
- Read the [API Reference](API_REFERENCE.md)

"""
        
        (output_path / "QUICK_START.md").write_text(quickstart)
        typer.echo("   ✅ Quick start guide generated")
    except Exception as e:
        typer.echo(f"   ⚠️  Quick start guide generation failed: {e}")
    
    typer.echo(f"\n✅ Documentation generated in: {output_path}")
    typer.echo(f"   Format: {format}")
    typer.echo(f"   Examples included: {include_examples}")
