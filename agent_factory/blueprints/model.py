"""
Blueprint model - Packaging system for agents, tools, and workflows.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class PricingModel(str, Enum):
    """Pricing models for blueprints."""

    FREE = "free"
    ONE_TIME = "one-time"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage-based"


@dataclass
class PricingInfo:
    """Pricing information for a blueprint."""

    model: PricingModel
    price: float = 0.0
    currency: str = "USD"
    period: str | None = None
    usage_unit: str | None = None


@dataclass
class BlueprintConfig:
    """Configuration for a blueprint."""

    dependencies: list[str] = field(default_factory=list)
    environment_variables: dict[str, str] = field(default_factory=dict)
    required_tools: list[str] = field(default_factory=list)
    required_agents: list[str] = field(default_factory=list)


@dataclass
class BlueprintMetadata:
    """Metadata for a blueprint."""

    demo_url: str = ""
    documentation: str = ""


@dataclass
class Blueprint:
    """
    Blueprint - A packaged agent configuration.

    Example:
        >>> blueprint = BlueprintLoader().load("blueprints/research_assistant/blueprint.yaml")
    """

    id: str
    name: str
    version: str
    description: str
    author: str
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)  # Agent IDs or paths
    tools: list[str] = field(default_factory=list)  # Tool IDs or paths
    workflows: list[str] = field(default_factory=list)  # Workflow IDs or paths
    knowledge_packs: list[str] = field(default_factory=list)  # Knowledge pack IDs
    config: BlueprintConfig = field(default_factory=BlueprintConfig)
    metadata: BlueprintMetadata = field(default_factory=BlueprintMetadata)
    pricing: PricingInfo = field(default_factory=lambda: PricingInfo(model=PricingModel.FREE))

    def to_dict(self) -> dict[str, Any]:
        """Serialize blueprint to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "agents": self.agents,
            "tools": self.tools,
            "workflows": self.workflows,
            "knowledge_packs": self.knowledge_packs,
            "config": {
                "dependencies": self.config.dependencies,
                "environment_variables": self.config.environment_variables,
                "required_tools": self.config.required_tools,
                "required_agents": self.config.required_agents,
            },
            "metadata": {
                "demo_url": self.metadata.demo_url,
                "documentation": self.metadata.documentation,
            },
            "pricing": {
                "model": self.pricing.model.value,
                "price": self.pricing.price,
                "currency": self.pricing.currency,
            },
        }

    def to_yaml(self) -> str:
        """Serialize blueprint to YAML."""
        data = {"blueprint": self.to_dict()}
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def package(self, output_dir: str) -> str:
        """
        Package this blueprint into a directory under output_dir.

        Creates <output_dir>/<id>/ containing blueprint.yaml plus the
        component directories (agents/, tools/, workflows/).

        Returns:
            Path to the package directory
        """
        base = Path(output_dir) / self.id
        for sub in ("agents", "tools", "workflows"):
            (base / sub).mkdir(parents=True, exist_ok=True)
        (base / "blueprint.yaml").write_text(self.to_yaml(), encoding="utf-8")
        return str(base)

    def install(self, target_dir: str) -> bool:
        """
        Install this blueprint into target_dir.

        Lays down the component directories and the blueprint manifest so
        the registry can load it from disk.

        Returns:
            True on success
        """
        base = Path(target_dir)
        for sub in ("agents", "tools", "workflows"):
            (base / sub).mkdir(parents=True, exist_ok=True)
        (base / "blueprint.yaml").write_text(self.to_yaml(), encoding="utf-8")
        return True
