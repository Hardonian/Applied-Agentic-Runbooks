"""
Blueprint model - Packaging system for agents, tools, and workflows.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import yaml
import json
from pathlib import Path

from agent_factory.agents.agent import Agent
from agent_factory.tools.base import Tool
from agent_factory.workflows.model import Workflow


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
    period: Optional[str] = None
    usage_unit: Optional[str] = None


@dataclass
class BlueprintConfig:
    """Configuration for a blueprint."""
    dependencies: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    required_tools: List[str] = field(default_factory=list)
    required_agents: List[str] = field(default_factory=list)


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
    tags: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)  # Agent IDs or paths
    tools: List[str] = field(default_factory=list)  # Tool IDs or paths
    workflows: List[str] = field(default_factory=list)  # Workflow IDs or paths
    knowledge_packs: List[str] = field(default_factory=list)  # Knowledge pack IDs
    config: BlueprintConfig = field(default_factory=BlueprintConfig)
    metadata: BlueprintMetadata = field(default_factory=BlueprintMetadata)
    pricing: PricingInfo = field(default_factory=lambda: PricingInfo(model=PricingModel.FREE))
    
    def to_dict(self) -> Dict[str, Any]:
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
            },
        }
    
    def to_yaml(self) -> str:
        """Serialize blueprint to YAML."""
        data = {"blueprint": self.to_dict()}
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Blueprint":
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
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "blueprint.yaml").write_text(self.to_yaml(), encoding="utf-8")
        return str(package_dir)

    def install(self, target_path: str) -> bool:
        """Install the manifest into a controlled target directory."""
        try:
            target = Path(target_path)
            target.mkdir(parents=True, exist_ok=True)
            (target / "blueprint.yaml").write_text(self.to_yaml(), encoding="utf-8")
            for component_dir in ("agents", "tools", "workflows"):
                (target / component_dir).mkdir(exist_ok=True)
            return True
        except OSError:
            return False
