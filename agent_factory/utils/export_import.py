"""Portable registry export/import utilities.

Definitions are serialized as data only. Tool callables remain trusted runtime
registrations and are never imported from an export artifact.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from agent_factory.agents.agent import Agent
from agent_factory.blueprints.model import Blueprint
from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.workflows.model import Workflow


def _registry(registry: Optional[LocalRegistry]) -> LocalRegistry:
    return registry or LocalRegistry()


def _validate_format(format: str) -> str:
    if format not in {"yaml", "json"}:
        raise ValueError("format must be 'yaml' or 'json'")
    return format


def _write_export(output_path: Path, data: Dict[str, Any], format: str) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if format == "yaml":
        output_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    else:
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def _read_export(import_path: Path) -> Dict[str, Any]:
    if not import_path.exists() or not import_path.is_file():
        raise FileNotFoundError(f"Import file not found: {import_path}")
    data = (
        yaml.safe_load(import_path.read_text(encoding="utf-8"))
        if import_path.suffix.lower() in {".yaml", ".yml"}
        else json.loads(import_path.read_text(encoding="utf-8"))
    )
    if not isinstance(data, dict):
        raise ValueError("Import artifact must contain an object")
    return data


def _envelope(kind: str, definition: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        kind: definition,
    }


def export_agent(
    agent_id: str,
    output_path: Optional[Path] = None,
    format: str = "yaml",
    *,
    registry: Optional[LocalRegistry] = None,
) -> Path:
    """Export a registered agent definition."""
    format = _validate_format(format)
    agent = _registry(registry).get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent not found: {agent_id}")
    return _write_export(
        output_path or Path(f"agents/{agent_id}.{format}"), _envelope("agent", agent.to_dict()), format
    )


def export_blueprint(
    blueprint_id: str,
    output_path: Optional[Path] = None,
    *,
    registry: Optional[LocalRegistry] = None,
) -> Path:
    """Export a blueprint manifest as ``blueprint.yaml``."""
    blueprint = _registry(registry).get_blueprint(blueprint_id)
    if not blueprint:
        raise ValueError(f"Blueprint not found: {blueprint_id}")
    destination = output_path or Path(f"blueprints/{blueprint_id}")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "blueprint.yaml").write_text(blueprint.to_yaml(), encoding="utf-8")
    return destination


def export_workflow(
    workflow_id: str,
    output_path: Optional[Path] = None,
    format: str = "yaml",
    *,
    registry: Optional[LocalRegistry] = None,
) -> Path:
    """Export a registered workflow definition."""
    format = _validate_format(format)
    workflow = _registry(registry).get_workflow(workflow_id)
    if not workflow:
        raise ValueError(f"Workflow not found: {workflow_id}")
    return _write_export(
        output_path or Path(f"workflows/{workflow_id}.{format}"),
        _envelope("workflow", workflow.to_dict()),
        format,
    )


def export_all(
    tenant_id: str,
    output_dir: Path,
    include_agents: bool = True,
    include_blueprints: bool = True,
    include_workflows: bool = True,
    *,
    registry: Optional[LocalRegistry] = None,
) -> Dict[str, List[Path]]:
    """Export all definitions from a caller-selected (tenant-scoped) registry.

    ``LocalRegistry`` itself has no tenant filter, so callers must pass a
    registry already scoped to ``tenant_id``. This prevents a global registry
    from being silently represented as tenant-isolated.
    """
    active_registry = _registry(registry)
    output_dir.mkdir(parents=True, exist_ok=True)
    exported: Dict[str, List[Path]] = {"agents": [], "blueprints": [], "workflows": []}
    if include_agents:
        exported["agents"] = [
            export_agent(agent_id, output_dir / "agents" / f"{agent_id}.yaml", registry=active_registry)
            for agent_id in active_registry.list_agents()
        ]
    if include_blueprints:
        exported["blueprints"] = [
            export_blueprint(blueprint_id, output_dir / "blueprints" / blueprint_id, registry=active_registry)
            for blueprint_id in active_registry.list_blueprints()
        ]
    if include_workflows:
        exported["workflows"] = [
            export_workflow(workflow_id, output_dir / "workflows" / f"{workflow_id}.yaml", registry=active_registry)
            for workflow_id in active_registry.list_workflows()
        ]
    return exported


def import_agent(import_path: Path, agent_id: Optional[str] = None, *, registry: Optional[LocalRegistry] = None) -> str:
    """Import an agent definition and register it in the selected registry."""
    data = _read_export(import_path)
    definition = data.get("agent", data)
    if not isinstance(definition, dict):
        raise ValueError("Agent import is missing an agent definition")
    definition = dict(definition)
    if agent_id:
        definition["id"] = agent_id
    agent = Agent.from_dict(definition)
    _registry(registry).register_agent(agent)
    return agent.id


def import_workflow(import_path: Path, workflow_id: Optional[str] = None, *, registry: Optional[LocalRegistry] = None) -> str:
    """Import a workflow definition and register it in the selected registry."""
    data = _read_export(import_path)
    definition = data.get("workflow", data)
    if not isinstance(definition, dict):
        raise ValueError("Workflow import is missing a workflow definition")
    definition = dict(definition)
    if workflow_id:
        definition["id"] = workflow_id
    workflow = Workflow.from_dict(definition)
    _registry(registry).register_workflow(workflow)
    return workflow.id


def import_blueprint(import_path: Path, *, registry: Optional[LocalRegistry] = None) -> str:
    """Import a blueprint manifest and register it in the selected registry."""
    blueprint_file = import_path / "blueprint.yaml" if import_path.is_dir() else import_path
    data = _read_export(blueprint_file)
    blueprint = Blueprint.from_dict(data.get("blueprint", data))
    _registry(registry).register_blueprint(blueprint)
    return blueprint.id
