"""
Blueprint system for packaging and distributing agent configurations.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from agent_factory.agents.agent import Agent
from agent_factory.core.tool import Tool
from agent_factory.core.workflow import Workflow


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
    period: str | None = None  # "monthly", "yearly" for subscriptions
    usage_unit: str | None = None  # For usage-based pricing


@dataclass
class BlueprintConfig:
    """Configuration for a blueprint."""

    dependencies: list[str] = field(default_factory=list)
    environment_variables: dict[str, str] = field(default_factory=dict)
    required_tools: list[str] = field(default_factory=list)
    required_agents: list[str] = field(default_factory=list)


@dataclass
class Blueprint:
    """
    Blueprint - A packaged agent configuration that can be installed and run.

    Example:
        >>> blueprint = Blueprint.from_yaml("blueprints/support_bot/blueprint.yaml")
        >>> blueprint.install("my_project")
    """

    id: str
    name: str
    version: str
    description: str
    author: str
    agents: list[Agent] = field(default_factory=list)
    tools: list[Tool] = field(default_factory=list)
    workflows: list[Workflow] = field(default_factory=list)
    config: BlueprintConfig = field(default_factory=BlueprintConfig)
    pricing: PricingInfo = field(default_factory=lambda: PricingInfo(model=PricingModel.FREE))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate blueprint after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate blueprint configuration."""
        if not self.id:
            raise ValueError("Blueprint ID is required")

        if not self.name:
            raise ValueError("Blueprint name is required")

        if not self.version:
            raise ValueError("Blueprint version is required")

        # Check that required agents exist
        for agent_id in self.config.required_agents:
            if not any(a.id == agent_id for a in self.agents):
                raise ValueError(f"Required agent not found: {agent_id}")

        # Check that required tools exist
        for tool_id in self.config.required_tools:
            if not any(t.id == tool_id for t in self.tools):
                raise ValueError(f"Required tool not found: {tool_id}")

    def package(self, output_path: str) -> str:
        """
        Package blueprint into a distributable format.

        Args:
            output_path: Directory to create package in

        Returns:
            Path to packaged blueprint
        """
        package_dir = Path(output_path) / f"{self.id}-{self.version}"
        package_dir.mkdir(parents=True, exist_ok=True)

        # Create blueprint.yaml
        blueprint_yaml = self.to_yaml()
        (package_dir / "blueprint.yaml").write_text(blueprint_yaml)

        # Create agents directory
        agents_dir = package_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        for agent in self.agents:
            agent_dict = agent.to_dict()
            (agents_dir / f"{agent.id}.json").write_text(json.dumps(agent_dict, indent=2))

        # Create tools directory
        tools_dir = package_dir / "tools"
        tools_dir.mkdir(exist_ok=True)
        for tool in self.tools:
            tool_dict = tool.to_dict()
            (tools_dir / f"{tool.id}.json").write_text(json.dumps(tool_dict, indent=2))

        # Create workflows directory
        workflows_dir = package_dir / "workflows"
        workflows_dir.mkdir(exist_ok=True)
        for workflow in self.workflows:
            workflow_dict = workflow.to_dict()
            (workflows_dir / f"{workflow.id}.json").write_text(json.dumps(workflow_dict, indent=2))

        # Create README
        readme = self._generate_readme()
        (package_dir / "README.md").write_text(readme)

        return str(package_dir)

    def install(self, target_path: str) -> bool:
        """
        Install blueprint to target path.

        Args:
            target_path: Directory to install blueprint

        Returns:
            True if installation successful
        """
        try:
            target = Path(target_path)
            target.mkdir(parents=True, exist_ok=True)

            # Copy agents
            agents_dir = target / "agents"
            agents_dir.mkdir(exist_ok=True)
            for agent in self.agents:
                agent_dict = agent.to_dict()
                (agents_dir / f"{agent.id}.json").write_text(json.dumps(agent_dict, indent=2))

            # Copy tools
            tools_dir = target / "tools"
            tools_dir.mkdir(exist_ok=True)
            for tool in self.tools:
                tool_dict = tool.to_dict()
                (tools_dir / f"{tool.id}.json").write_text(json.dumps(tool_dict, indent=2))

            # Copy workflows
            workflows_dir = target / "workflows"
            workflows_dir.mkdir(exist_ok=True)
            for workflow in self.workflows:
                workflow_dict = workflow.to_dict()
                (workflows_dir / f"{workflow.id}.json").write_text(
                    json.dumps(workflow_dict, indent=2)
                )

            # Create .env.example
            env_example = self._generate_env_example()
            (target / ".env.example").write_text(env_example)

            return True

        except Exception as e:
            print(f"Installation failed: {e}")
            return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize blueprint to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "agents": [agent.to_dict() for agent in self.agents],
            "tools": [tool.to_dict() for tool in self.tools],
            "workflows": [workflow.to_dict() for workflow in self.workflows],
            "config": {
                "dependencies": self.config.dependencies,
                "environment_variables": self.config.environment_variables,
                "required_tools": self.config.required_tools,
                "required_agents": self.config.required_agents,
            },
            "pricing": {
                "model": self.pricing.model.value,
                "price": self.pricing.price,
                "currency": self.pricing.currency,
                "period": self.pricing.period,
            },
            "metadata": self.metadata,
        }

    def to_yaml(self) -> str:
        """Serialize blueprint to YAML."""
        data = self.to_dict()
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Blueprint":
        """
        Load blueprint from YAML file.

        Args:
            yaml_path: Path to blueprint.yaml file

        Returns:
            Blueprint instance
        """
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            raise FileNotFoundError(f"Blueprint file not found: {yaml_path}")

        data = yaml.safe_load(yaml_file.read_text())
        return cls.from_dict(data, yaml_file.parent)

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_path: Path | None = None) -> "Blueprint":
        """
        Create blueprint from dictionary.

        Args:
            data: Blueprint data dictionary
            base_path: Base path for loading related files

        Returns:
            Blueprint instance
        """
        from agent_factory.agents.agent import Agent
        from agent_factory.core.workflow import Workflow

        # Load agents
        agents = []
        if base_path:
            agents_dir = base_path / "agents"
            if agents_dir.exists():
                for agent_file in agents_dir.glob("*.json"):
                    try:
                        agent_data = json.loads(agent_file.read_text())
                        agents.append(Agent.from_dict(agent_data))
                    except Exception as e:
                        print(f"Warning: Could not load agent {agent_file}: {e}")

        # Also try loading from data dict
        if "agents" in data and isinstance(data["agents"], list):
            for agent_data in data["agents"]:
                try:
                    agents.append(Agent.from_dict(agent_data))
                except Exception as e:
                    print(f"Warning: Could not load agent from data: {e}")

        # Load tools from blueprint directory
        tools = []
        if base_path:
            tools_dir = base_path / "tools"
            if tools_dir.exists():
                for tool_file in tools_dir.glob("*.json"):
                    try:
                        tool_data = json.loads(tool_file.read_text())
                        # Create placeholder tool (implementation needs to be registered)
                        from agent_factory.core.tool import Tool

                        def placeholder_impl(**kwargs):
                            raise NotImplementedError(
                                f"Tool {tool_data.get('id')} implementation not available. "
                                "Please register the tool with its implementation."
                            )

                        tool = Tool(
                            id=tool_data.get("id", tool_file.stem),
                            name=tool_data.get("name", tool_file.stem),
                            description=tool_data.get("description", ""),
                            implementation=placeholder_impl,
                        )
                        tools.append(tool)
                    except Exception as e:
                        print(f"Warning: Could not load tool {tool_file}: {e}")

        # Load workflows
        workflows = []
        if base_path:
            workflows_dir = base_path / "workflows"
            if workflows_dir.exists():
                for workflow_file in workflows_dir.glob("*.json"):
                    try:
                        workflow_data = json.loads(workflow_file.read_text())
                        # Reconstruct workflow steps
                        from agent_factory.core.workflow import Condition, WorkflowStep

                        steps = []
                        for step_data in workflow_data.get("steps", []):
                            condition = None
                            if step_data.get("condition"):
                                cond_data = step_data["condition"]
                                condition = Condition(
                                    expression=cond_data.get("expression", ""),
                                    description=cond_data.get("description"),
                                )

                            step = WorkflowStep(
                                id=step_data.get("id", ""),
                                agent_id=step_data.get("agent_id", ""),
                                input_mapping=step_data.get("input_mapping", {}),
                                output_mapping=step_data.get("output_mapping", {}),
                                condition=condition,
                                timeout=step_data.get("timeout", 30),
                                retry_attempts=step_data.get("retry_attempts", 3),
                            )
                            steps.append(step)

                        workflow = Workflow(
                            id=workflow_data.get("id", workflow_file.stem),
                            name=workflow_data.get("name", ""),
                            steps=steps,
                        )
                        workflows.append(workflow)
                    except Exception as e:
                        print(f"Warning: Could not load workflow {workflow_file}: {e}")

        # Also try loading from data dict
        if "workflows" in data and isinstance(data["workflows"], list):
            for workflow_data in data["workflows"]:
                try:
                    from agent_factory.core.workflow import Condition, WorkflowStep

                    steps = []
                    for step_data in workflow_data.get("steps", []):
                        condition = None
                        if step_data.get("condition"):
                            cond_data = step_data["condition"]
                            condition = Condition(
                                expression=cond_data.get("expression", ""),
                                description=cond_data.get("description"),
                            )

                        step = WorkflowStep(
                            id=step_data.get("id", ""),
                            agent_id=step_data.get("agent_id", ""),
                            input_mapping=step_data.get("input_mapping", {}),
                            output_mapping=step_data.get("output_mapping", {}),
                            condition=condition,
                            timeout=step_data.get("timeout", 30),
                            retry_attempts=step_data.get("retry_attempts", 3),
                        )
                        steps.append(step)

                    workflow = Workflow(
                        id=workflow_data.get("id", ""),
                        name=workflow_data.get("name", ""),
                        steps=steps,
                    )
                    workflows.append(workflow)
                except Exception as e:
                    print(f"Warning: Could not load workflow from data: {e}")

        # Create config
        config_data = data.get("config", {})
        config = BlueprintConfig(
            dependencies=config_data.get("dependencies", []),
            environment_variables=config_data.get("environment_variables", {}),
            required_tools=config_data.get("required_tools", []),
            required_agents=config_data.get("required_agents", []),
        )

        # Create pricing
        pricing_data = data.get("pricing", {})
        pricing = PricingInfo(
            model=PricingModel(pricing_data.get("model", "free")),
            price=pricing_data.get("price", 0.0),
            currency=pricing_data.get("currency", "USD"),
            period=pricing_data.get("period"),
        )

        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data.get("author", "unknown"),
            agents=agents,
            tools=tools,
            workflows=workflows,
            config=config,
            pricing=pricing,
            metadata=data.get("metadata", {}),
        )

    def _generate_readme(self) -> str:
        """
        Generate README for blueprint.

        Returns:
            README content as string
        """
        env_vars_section = ""
        if self.config.environment_variables:
            env_vars_section = (
                "\n## Configuration\n\nRequired environment variables:\n"
                + "\n".join(f"- `{k}`: {v}" for k, v in self.config.environment_variables.items())
            )

        return f"""# {self.name}

{self.description}

## Version

{self.version}

## Author

{self.author}

## Installation

```bash
agent-factory blueprint install {self.id}
```
{env_vars_section}
## Usage

[Usage instructions would go here]

## Pricing

{self.pricing.model.value}: ${self.pricing.price} {self.pricing.currency}
"""

    def _generate_env_example(self) -> str:
        """
        Generate .env.example file content.

        Returns:
            .env.example content as string
        """
        lines = ["# Blueprint Configuration", ""]
        for key, description in self.config.environment_variables.items():
            lines.append(f"# {description}")
            lines.append(f"{key}=")
            lines.append("")
        return "\n".join(lines)
