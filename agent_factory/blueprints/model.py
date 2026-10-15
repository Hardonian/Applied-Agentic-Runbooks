"""
Blueprint model - Packaging system for agents, tools, and workflows.
"""

import json
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
    agents: list[Any] = field(default_factory=list)  # Definitions or IDs
    tools: list[Any] = field(default_factory=list)  # Definitions or IDs
    workflows: list[Any] = field(default_factory=list)  # Definitions or IDs
    knowledge_packs: list[str] = field(default_factory=list)  # Knowledge pack IDs
    config: BlueprintConfig = field(default_factory=BlueprintConfig)
    metadata: BlueprintMetadata = field(default_factory=BlueprintMetadata)
    pricing: PricingInfo = field(default_factory=lambda: PricingInfo(model=PricingModel.FREE))

    def __post_init__(self) -> None:
        """Normalize API-provided metadata into the portable model."""
        if isinstance(self.metadata, dict):
            self.metadata = BlueprintMetadata(
                demo_url=self.metadata.get("demo_url", ""),
                documentation=self.metadata.get("documentation", ""),
            )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize blueprint to dictionary."""
        def serialize_component(component: Any) -> Any:
            return component.to_dict() if hasattr(component, "to_dict") else component

        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "agents": [serialize_component(agent) for agent in self.agents],
            "tools": [serialize_component(tool) for tool in self.tools],
            "workflows": [serialize_component(workflow) for workflow in self.workflows],
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
                "period": self.pricing.period,
                "usage_unit": self.pricing.usage_unit,
            },
        }
    
    def to_yaml(self) -> str:
        """Serialize blueprint to YAML."""
        data = {"blueprint": self.to_dict()}
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Blueprint":
        """Build a blueprint from its portable YAML/JSON representation."""
        config_data = data.get("config", {})
        metadata_data = data.get("metadata", {})
        pricing_data = data.get("pricing", {})
        return cls(
            id=data["id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", "unknown"),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            agents=data.get("agents", []),
            tools=data.get("tools", []),
            workflows=data.get("workflows", []),
            knowledge_packs=data.get("knowledge_packs", []),
            config=BlueprintConfig(
                dependencies=config_data.get("dependencies", []),
                environment_variables=config_data.get("environment_variables", {}),
                required_tools=config_data.get("required_tools", []),
                required_agents=config_data.get("required_agents", []),
            ),
            metadata=BlueprintMetadata(
                demo_url=metadata_data.get("demo_url", ""),
                documentation=metadata_data.get("documentation", ""),
            ),
            pricing=PricingInfo(
                model=PricingModel(pricing_data.get("model", PricingModel.FREE.value)),
                price=pricing_data.get("price", 0.0),
                currency=pricing_data.get("currency", "USD"),
                period=pricing_data.get("period"),
                usage_unit=pricing_data.get("usage_unit"),
            ),
        )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Blueprint":
        """Load a blueprint package manifest from disk."""
        path = Path(yaml_path)
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.from_dict(data.get("blueprint", data))

    def package(self, output_path: str) -> str:
        """Create a portable blueprint package directory."""
        package_dir = Path(output_path) / f"{self.id}-{self.version}"
        self._write_installation(package_dir, include_readme=True)
        return str(package_dir)

    def install(self, target_path: str) -> bool:
        """Install the manifest into a controlled target directory."""
        try:
            target = Path(target_path)
            self._write_installation(target, include_readme=True)
            return True
        except (OSError, TypeError, ValueError):
            return False

    def _write_installation(self, target: Path, *, include_readme: bool) -> None:
        """Write a complete, code-free portable blueprint installation."""
        target.mkdir(parents=True, exist_ok=True)
        (target / "blueprint.yaml").write_text(self.to_yaml(), encoding="utf-8")

        component_groups = {
            "agents": self.agents,
            "tools": self.tools,
            "workflows": self.workflows,
        }
        for directory_name, components in component_groups.items():
            component_dir = target / directory_name
            component_dir.mkdir(exist_ok=True)
            for index, component in enumerate(components):
                component_data = self._serialize_component(component)
                component_id = str(component_data.get("id") or f"{directory_name}-{index + 1}")
                self._validate_component_id(component_id)
                component_data.setdefault("id", component_id)
                (component_dir / f"{component_id}.json").write_text(
                    json.dumps(component_data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

        (target / ".env.example").write_text(self._env_example(), encoding="utf-8")
        if include_readme:
            (target / "README.md").write_text(self._readme(), encoding="utf-8")

    @staticmethod
    def _serialize_component(component: Any) -> dict[str, Any]:
        """Convert a component definition to safe JSON-package data."""
        if isinstance(component, str):
            return {"id": component}
        if isinstance(component, dict):
            return dict(component)
        if hasattr(component, "to_dict"):
            component_data = component.to_dict()
            if isinstance(component_data, dict):
                return component_data
        raise TypeError("Blueprint components must be IDs, dictionaries, or serializable objects")

    @staticmethod
    def _validate_component_id(component_id: str) -> None:
        """Prevent a component ID from escaping its package directory."""
        if not component_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in component_id):
            raise ValueError(f"Unsafe blueprint component ID: {component_id!r}")

    def _env_example(self) -> str:
        """Create an env template without copying any supplied secret values."""
        if not self.config.environment_variables:
            return "# No environment variables are required.\n"
        lines = ["# Populate these values in your deployment environment."]
        for name, description in self.config.environment_variables.items():
            lines.append(f"# {description}")
            lines.append(f"{name}=")
        return "\n".join(lines) + "\n"

    def _readme(self) -> str:
        """Provide basic operational instructions with every package."""
        dependencies = "\n".join(f"- `{dependency}`" for dependency in self.config.dependencies) or "- None"
        return (
            f"# {self.name}\n\n{self.description}\n\n"
            f"Version: `{self.version}`\n\n"
            "## Contents\n\n"
            "- `blueprint.yaml`: portable manifest\n"
            "- `agents/`, `tools/`, `workflows/`: JSON component definitions\n"
            "- `.env.example`: required configuration keys (without values)\n\n"
            f"## Dependencies\n\n{dependencies}\n"
        )
