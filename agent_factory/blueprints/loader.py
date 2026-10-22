"""
Load blueprints from YAML/JSON files.
"""

from pathlib import Path

import yaml

from agent_factory.blueprints.model import (
    Blueprint,
    BlueprintConfig,
    BlueprintMetadata,
    PricingInfo,
    PricingModel,
)


class BlueprintLoader:
    """Load blueprints from files."""

    def load(self, blueprint_path: str) -> Blueprint:
        """
        Load blueprint from YAML file.

        Args:
            blueprint_path: Path to blueprint.yaml file

        Returns:
            Loaded Blueprint
        """
        blueprint_path = Path(blueprint_path)
        if not blueprint_path.exists():
            raise FileNotFoundError(f"Blueprint not found: {blueprint_path}")

        with open(blueprint_path) as f:
            data = yaml.safe_load(f)

        blueprint_data = data.get("blueprint", {})

        # Parse config
        config_data = blueprint_data.get("config", {})
        config = BlueprintConfig(
            dependencies=config_data.get("dependencies", []),
            environment_variables=config_data.get("environment_variables", {}),
            required_tools=config_data.get("required_tools", []),
            required_agents=config_data.get("required_agents", []),
        )

        # Parse metadata
        metadata_data = blueprint_data.get("metadata", {})
        metadata = BlueprintMetadata(
            demo_url=metadata_data.get("demo_url", ""),
            documentation=metadata_data.get("documentation", ""),
        )

        # Parse pricing
        pricing_data = blueprint_data.get("pricing", {})
        pricing = PricingInfo(
            model=PricingModel(pricing_data.get("model", "free")),
            price=pricing_data.get("price", 0.0),
            currency=pricing_data.get("currency", "USD"),
            period=pricing_data.get("period"),
        )

        return Blueprint(
            id=blueprint_data.get("id", ""),
            name=blueprint_data.get("name", ""),
            version=blueprint_data.get("version", "1.0.0"),
            description=blueprint_data.get("description", ""),
            author=blueprint_data.get("author", "unknown"),
            category=blueprint_data.get("category", "general"),
            tags=blueprint_data.get("tags", []),
            agents=blueprint_data.get("agents", []),
            tools=blueprint_data.get("tools", []),
            workflows=blueprint_data.get("workflows", []),
            knowledge_packs=blueprint_data.get("knowledge_packs", []),
            config=config,
            metadata=metadata,
            pricing=pricing,
        )
