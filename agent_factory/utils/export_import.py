"""
Export/Import utilities for agents, blueprints, and workflows.

Increases switching costs by making it easy to export/import data.
"""

import json
from datetime import datetime
from pathlib import Path

import yaml

from agent_factory.blueprints.loader import load_blueprint


def export_agent(
    agent_id: str,
    output_path: Path | None = None,
    format: str = "yaml",
) -> Path:
    """
    Export an agent to a file.

    Args:
        agent_id: Agent ID to export
        output_path: Output file path (defaults to agents/{agent_id}.yaml)
        format: Export format (yaml, json)

    Returns:
        Path to exported file
    """
    # TODO: Load agent from registry
    # For now, this is a placeholder structure

    if not output_path:
        output_path = Path(f"agents/{agent_id}.{format}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Placeholder export structure
    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "agent": {
            "id": agent_id,
            # TODO: Add actual agent data
        },
    }

    if format == "yaml":
        with open(output_path, "w") as f:
            yaml.dump(export_data, f, default_flow_style=False)
    else:
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

    return output_path


def export_blueprint(
    blueprint_id: str,
    output_path: Path | None = None,
) -> Path:
    """
    Export a blueprint to a file.

    Args:
        blueprint_id: Blueprint ID to export
        output_path: Output directory path (defaults to blueprints/{blueprint_id}/)

    Returns:
        Path to exported blueprint directory
    """
    if not output_path:
        output_path = Path(f"blueprints/{blueprint_id}/")

    output_path.mkdir(parents=True, exist_ok=True)

    # Load blueprint
    try:
        blueprint = load_blueprint(blueprint_id)

        # Export blueprint.yaml
        blueprint_file = output_path / "blueprint.yaml"
        with open(blueprint_file, "w") as f:
            yaml.dump(blueprint.to_dict(), f, default_flow_style=False)

        return output_path
    except Exception as e:
        raise ValueError(f"Failed to export blueprint {blueprint_id}: {e}") from e


def export_workflow(
    workflow_id: str,
    output_path: Path | None = None,
    format: str = "yaml",
) -> Path:
    """
    Export a workflow to a file.

    Args:
        workflow_id: Workflow ID to export
        output_path: Output file path (defaults to workflows/{workflow_id}.yaml)
        format: Export format (yaml, json)

    Returns:
        Path to exported file
    """
    if not output_path:
        output_path = Path(f"workflows/{workflow_id}.{format}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # TODO: Load workflow from registry
    # Placeholder export structure
    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "workflow": {
            "id": workflow_id,
            # TODO: Add actual workflow data
        },
    }

    if format == "yaml":
        with open(output_path, "w") as f:
            yaml.dump(export_data, f, default_flow_style=False)
    else:
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

    return output_path


def export_all(
    tenant_id: str,
    output_dir: Path,
    include_agents: bool = True,
    include_blueprints: bool = True,
    include_workflows: bool = True,
) -> dict[str, list[Path]]:
    """
    Export all agents, blueprints, and workflows for a tenant.

    Args:
        tenant_id: Tenant ID
        output_dir: Output directory
        include_agents: Whether to export agents
        include_blueprints: Whether to export blueprints
        include_workflows: Whether to export workflows

    Returns:
        Dictionary mapping type to list of exported file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    exported = {
        "agents": [],
        "blueprints": [],
        "workflows": [],
    }

    # TODO: Get all agents/blueprints/workflows for tenant
    # For now, this is a placeholder structure

    if include_agents:
        agents_dir = output_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        # TODO: Export agents

    if include_blueprints:
        blueprints_dir = output_dir / "blueprints"
        blueprints_dir.mkdir(exist_ok=True)
        # TODO: Export blueprints

    if include_workflows:
        workflows_dir = output_dir / "workflows"
        workflows_dir.mkdir(exist_ok=True)
        # TODO: Export workflows

    return exported


def import_agent(
    import_path: Path,
    agent_id: str | None = None,
) -> str:
    """
    Import an agent from a file.

    Args:
        import_path: Path to agent file
        agent_id: Optional agent ID (if different from file)

    Returns:
        Imported agent ID
    """
    # TODO: Implement agent import
    # For now, this is a placeholder
    raise NotImplementedError("Agent import not yet implemented")


def import_blueprint(
    import_path: Path,
) -> str:
    """
    Import a blueprint from a directory or file.

    Args:
        import_path: Path to blueprint directory or file

    Returns:
        Imported blueprint ID
    """
    if import_path.is_dir():
        blueprint_file = import_path / "blueprint.yaml"
    else:
        blueprint_file = import_path

    if not blueprint_file.exists():
        raise FileNotFoundError(f"Blueprint file not found: {blueprint_file}")

    # Load blueprint
    blueprint = load_blueprint(str(blueprint_file))

    # TODO: Register blueprint in registry

    return blueprint.id
