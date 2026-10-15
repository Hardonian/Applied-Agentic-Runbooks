"""CLI commands package."""

from agent_factory.cli.commands import (
    agent,
    blueprint,
    config,
    docs,
    doctor,
    registry,
    tool,
    workflow,
)

# Import marketplace if available
try:
    from agent_factory.cli.commands import marketplace
except ImportError:
    marketplace = None

# Import execution if available
try:
    from agent_factory.cli.commands import execution
except ImportError:
    execution = None

# Import metrics if available
try:
    from agent_factory.cli.commands import metrics
except ImportError:
    metrics = None

# Import export if available
try:
    from agent_factory.cli.commands import export
except ImportError:
    export = None

__all__ = ["agent", "blueprint", "config", "docs", "doctor", "execution", "export", "marketplace", "metrics", "registry", "tool", "workflow"]
