"""
Blueprint service - Business logic for blueprint operations.
"""

from typing import Any

from agent_factory.blueprints.loader import BlueprintLoader
from agent_factory.blueprints.model import Blueprint
from agent_factory.registry.local_registry import LocalRegistry


class BlueprintService:
    """Service for blueprint operations."""

    def __init__(self, registry: LocalRegistry | None = None):
        """
        Initialize blueprint service.

        Args:
            registry: Registry instance (optional)
        """
        self.registry = registry or LocalRegistry()
        self.loader = BlueprintLoader()

    def load_blueprint(self, blueprint_path: str) -> Blueprint:
        """
        Load a blueprint from file.

        Args:
            blueprint_path: Path to blueprint.yaml

        Returns:
            Loaded blueprint
        """
        return self.loader.load(blueprint_path)

    def install_blueprint(
        self, blueprint: Blueprint, tenant_id: str | None = None
    ) -> dict[str, Any]:
        """
        Install a blueprint.

        Args:
            blueprint: Blueprint to install
            tenant_id: Optional tenant ID

        Returns:
            Installation result
        """
        # Register agents, tools, workflows from blueprint
        result = {
            "agents_installed": [],
            "tools_installed": [],
            "workflows_installed": [],
        }

        # Install agents
        for agent_id in blueprint.agents:
            # Load and register agent
            # Implementation would load from blueprint directory
            result["agents_installed"].append(agent_id)

        # Install tools
        for tool_id in blueprint.tools:
            result["tools_installed"].append(tool_id)

        # Install workflows
        for workflow_id in blueprint.workflows:
            result["workflows_installed"].append(workflow_id)

        return result

    def get_blueprint(self, blueprint_id: str) -> Blueprint | None:
        """
        Get blueprint by ID.

        Args:
            blueprint_id: Blueprint ID

        Returns:
            Blueprint if found, None otherwise
        """
        return self.registry.get_blueprint(blueprint_id)

    def list_blueprints(self) -> list[str]:
        """
        List all blueprint IDs.

        Returns:
            List of blueprint IDs
        """
        return self.registry.list_blueprints()
