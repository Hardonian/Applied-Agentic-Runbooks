"""
Main notebook converter implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_factory.blueprints.model import Blueprint

from agent_factory.notebook_converter.detector import AgentDetector, ToolDetector, WorkflowDetector
from agent_factory.notebook_converter.parser import NotebookParser
from agent_factory.notebook_converter.writer import AgentWriter, ToolWriter, WorkflowWriter


@dataclass
class ConversionResult:
    """Result of notebook conversion."""
    agents_created: list[str]
    tools_created: list[str]
    workflows_created: list[str]
    blueprint_created: str | None = None
    errors: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class NotebookConverter:
    """
    Convert Jupyter notebooks to Agent Factory agents, tools, and workflows.
    
    Example:
        >>> converter = NotebookConverter()
        >>> result = converter.convert("notebook.ipynb", agent_name="research-assistant")
        >>> print(f"Created {len(result.agents_created)} agents")
    """
    
    def __init__(self, output_dir: str = "./agent_factory"):
        """
        Initialize the converter.
        
        Args:
            output_dir: Base directory for output files
        """
        self.output_dir = Path(output_dir)
        self.parser = NotebookParser()
        self.agent_detector = AgentDetector()
        self.tool_detector = ToolDetector()
        self.workflow_detector = WorkflowDetector()
        self.agent_writer = AgentWriter(self.output_dir)
        self.tool_writer = ToolWriter(self.output_dir)
        self.workflow_writer = WorkflowWriter(self.output_dir)
    
    def convert(
        self,
        notebook_path: str | Path,
        agent_name: str | None = None,
        create_blueprint: bool = False,
        interactive: bool = False,
    ) -> ConversionResult:
        """
        Convert a notebook to agents, tools, and workflows.
        
        Args:
            notebook_path: Path to .ipynb file
            agent_name: Optional name for extracted agent
            create_blueprint: Whether to create a blueprint.yaml
            interactive: Whether to prompt for confirmations
        
        Returns:
            ConversionResult with created files and errors
        """
        nb_path = Path(notebook_path)
        if not nb_path.exists():
            raise FileNotFoundError(f"Notebook not found: {nb_path}")
        
        # Parse notebook
        notebook_data = self.parser.parse(nb_path)
        
        # Detect agents, tools, workflows
        agents = self.agent_detector.detect(notebook_data)
        tools = self.tool_detector.detect(notebook_data)
        workflows = self.workflow_detector.detect(notebook_data)
        
        # Interactive confirmation
        if interactive:
            self._confirm_detections(agents, tools, workflows)
        
        # Write files
        result = ConversionResult(
            agents_created=[],
            tools_created=[],
            workflows_created=[],
        )
        
        # Write agents
        for agent_def in agents:
            try:
                agent_id = agent_name or agent_def.get("id") or agent_def.get("name", "agent").lower().replace(" ", "-")
                agent_path = self.agent_writer.write(agent_id, agent_def)
                result.agents_created.append(str(agent_path))
            except Exception as e:
                result.errors.append(f"Failed to write agent {agent_def.get('name')}: {e}")
        
        # Write tools
        for tool_def in tools:
            try:
                tool_id = tool_def.get("id") or tool_def.get("name", "tool").lower().replace(" ", "-")
                tool_path = self.tool_writer.write(tool_id, tool_def)
                result.tools_created.append(str(tool_path))
            except Exception as e:
                result.errors.append(f"Failed to write tool {tool_def.get('name')}: {e}")
        
        # Write workflows
        for workflow_def in workflows:
            try:
                workflow_id = workflow_def.get("id") or workflow_def.get("name", "workflow").lower().replace(" ", "-")
                workflow_path = self.workflow_writer.write(workflow_id, workflow_def)
                result.workflows_created.append(str(workflow_path))
            except Exception as e:
                result.errors.append(f"Failed to write workflow {workflow_def.get('name')}: {e}")
        
        # Create blueprint if requested
        if create_blueprint and (result.agents_created or result.tools_created or result.workflows_created):
            try:
                blueprint_name = agent_name or "converted-blueprint"
                blueprint_path = self._create_blueprint(
                    blueprint_name,
                    result.agents_created,
                    result.tools_created,
                    result.workflows_created,
                )
                result.blueprint_created = str(blueprint_path)
            except Exception as e:
                result.errors.append(f"Failed to create blueprint: {e}")
        
        return result
    
    def _confirm_detections(self, agents: list[dict], tools: list[dict], workflows: list[dict]) -> None:
        """Prompt user to confirm detections (placeholder for interactive mode)."""
        print("\nDetected:")
        print(f"  Agents: {len(agents)}")
        print(f"  Tools: {len(tools)}")
        print(f"  Workflows: {len(workflows)}")
        # In full implementation, would prompt for confirmation
    
    def _create_blueprint(
        self,
        name: str,
        agent_paths: list[str],
        tool_paths: list[str],
        workflow_paths: list[str],
    ) -> Path:
        """Create a blueprint.yaml from converted components."""
        from agent_factory.blueprints.model import Blueprint, BlueprintConfig, BlueprintMetadata
        
        blueprint_dir = self.output_dir.parent / "blueprints" / name
        blueprint_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract agent/tool/workflow IDs from paths
        agent_ids = [Path(p).stem.replace("_config", "") for p in agent_paths]
        tool_ids = [Path(p).stem for p in tool_paths]
        workflow_ids = [Path(p).stem.replace("_workflow", "") for p in workflow_paths]
        
        blueprint = Blueprint(
            id=name,
            name=name.replace("-", " ").title(),
            version="1.0.0",
            description="Blueprint converted from notebook",
            author="Agent Factory",
            category="converted",
            tags=["converted", "notebook"],
            agents=agent_ids,
            tools=tool_ids,
            workflows=workflow_ids,
            knowledge_packs=[],
            config=BlueprintConfig(
                dependencies=[],
                environment_variables={},
                required_tools=tool_ids[:1] if tool_ids else [],
                required_agents=agent_ids[:1] if agent_ids else [],
            ),
            metadata=BlueprintMetadata(
                demo_url="",
                documentation="",
            ),
        )
        
        # Write blueprint.yaml
        blueprint_path = blueprint_dir / "blueprint.yaml"
        self._write_blueprint_yaml(blueprint_path, blueprint)
        
        return blueprint_path
    
    def _write_blueprint_yaml(self, path: Path, blueprint: "Blueprint") -> None:
        """Write blueprint to YAML file."""
        import yaml
        
        blueprint_dict = {
            "blueprint": {
                "id": blueprint.id,
                "name": blueprint.name,
                "version": blueprint.version,
                "description": blueprint.description,
                "author": blueprint.author,
                "category": blueprint.category,
                "tags": blueprint.tags,
                "agents": blueprint.agents,
                "tools": blueprint.tools,
                "workflows": blueprint.workflows,
                "knowledge_packs": blueprint.knowledge_packs,
                "config": {
                    "dependencies": blueprint.config.dependencies,
                    "environment_variables": blueprint.config.environment_variables,
                    "required_tools": blueprint.config.required_tools,
                    "required_agents": blueprint.config.required_agents,
                },
                "metadata": {
                    "demo_url": blueprint.metadata.demo_url,
                    "documentation": blueprint.metadata.documentation,
                },
            }
        }
        
        with open(path, "w") as f:
            yaml.dump(blueprint_dict, f, default_flow_style=False)
