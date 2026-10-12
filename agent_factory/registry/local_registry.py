"""
Local file-based registry for agents, tools, workflows, and blueprints.
"""

from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
import json
import yaml
import os

from agent_factory.agents.agent import Agent
from agent_factory.tools.base import Tool
from agent_factory.workflows.model import Workflow
from agent_factory.blueprints.model import Blueprint
from agent_factory.cache import get_cache


class LocalRegistry:
    """
    Local file-based registry for storing and retrieving agents, tools, workflows, and blueprints.
    
    Example:
        >>> registry = LocalRegistry("~/.agent_factory")
        >>> registry.register_agent(agent)
        >>> agent = registry.get_agent("research-assistant")
    """
    
    def __init__(
        self,
        base_path: str = "~/.agent_factory",
        tool_implementations: Optional[Dict[str, Callable[..., Any]]] = None,
    ):
        """
        Initialize local registry.
        
        Args:
            base_path: Base directory for registry storage
            tool_implementations: Runtime-only implementations keyed by tool
                ID. Callables are intentionally not serialized; callers must
                register trusted implementations at process start.
        """
        self.base_path = Path(base_path).expanduser()
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "agents").mkdir(exist_ok=True)
        (self.base_path / "tools").mkdir(exist_ok=True)
        (self.base_path / "workflows").mkdir(exist_ok=True)
        (self.base_path / "blueprints").mkdir(exist_ok=True)
        
        # Initialize cache
        self.cache = get_cache()
        self.cache_ttl = int(os.getenv("REGISTRY_CACHE_TTL", "3600"))  # 1 hour default
        self.tool_implementations = dict(tool_implementations or {})

    def register_tool_implementation(self, tool_id: str, implementation: Callable[..., Any]) -> None:
        """Register a trusted runtime implementation for a persisted tool."""
        self.tool_implementations[tool_id] = implementation
        self.cache.delete(f"tool:{tool_id}")
    
    # Agent methods
    def register_agent(self, agent: Agent) -> None:
        """Register an agent in the registry."""
        agent_file = self.base_path / "agents" / f"{agent.id}.json"
        agent_file.write_text(json.dumps(agent.to_dict(), indent=2))
        
        # Invalidate cache
        self.cache.delete(f"agent:{agent.id}")
        self.cache.delete("agents:list")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID with caching."""
        cache_key = f"agent:{agent_id}"
        
        # Try cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return Agent.from_dict(cached_data)
        
        # Load from file
        agent_file = self.base_path / "agents" / f"{agent_id}.json"
        if not agent_file.exists():
            return None
        
        data = json.loads(agent_file.read_text())
        agent = Agent.from_dict(data)
        
        # Cache the agent data
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
        
        return agent
    
    def list_agents(self) -> List[str]:
        """List all registered agent IDs with caching."""
        cache_key = "agents:list"
        
        # Try cache first
        cached_list = self.cache.get(cache_key)
        if cached_list:
            return cached_list
        
        # Load from filesystem
        agents_dir = self.base_path / "agents"
        agent_list = [f.stem for f in agents_dir.glob("*.json")]
        
        # Cache the list
        self.cache.set(cache_key, agent_list, ttl=self.cache_ttl)
        
        return agent_list
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent from the registry."""
        agent_file = self.base_path / "agents" / f"{agent_id}.json"
        if agent_file.exists():
            agent_file.unlink()
            # Invalidate cache
            self.cache.delete(f"agent:{agent_id}")
            self.cache.delete("agents:list")
            return True
        return False
    
    # Tool methods
    def register_tool(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        tool_file = self.base_path / "tools" / f"{tool.id}.json"
        tool_file.write_text(json.dumps(tool.to_dict(), indent=2))
        
        # Invalidate cache
        self.cache.delete(f"tool:{tool.id}")
        self.cache.delete("tools:list")
        self.tool_implementations[tool.id] = tool._implementation
    
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """
        Get a tool by ID with caching.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool instance or None
        """
        cache_key = f"tool:{tool_id}"
        
        # Try cache first. The serialized definition is cacheable; the callable
        # is resolved from the trusted in-process catalog every time.
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return self._deserialize_tool(tool_id, cached_data)
        
        tool_file = self.base_path / "tools" / f"{tool_id}.json"
        if not tool_file.exists():
            return None
        
        try:
            data = json.loads(tool_file.read_text())
            tool = self._deserialize_tool(tool_id, data)
            self.cache.set(cache_key, data, ttl=self.cache_ttl)
            return tool
        except Exception as e:
            # Log error but don't fail completely
            import logging
            logging.warning(f"Failed to load tool {tool_id}: {e}")
            return None

    def _deserialize_tool(self, tool_id: str, data: Dict[str, Any]) -> Tool:
        """Rebuild a persisted tool definition and attach a trusted callable."""
        from agent_factory.tools.base import ParameterSchema, ToolMetadata

        definition_id = data.get("id", tool_id)
        schema = data.get("schema", {})
        parameters_schema = schema.get("parameters", {})
        metadata_dict = data.get("metadata", schema.get("metadata", {}))
        parameter_schemas = {
            name: ParameterSchema(
                name=name,
                type=value.get("type", "string"),
                description=value.get("description", ""),
                required=name in parameters_schema.get("required", []),
                default=value.get("default"),
                enum=value.get("enum"),
            )
            for name, value in parameters_schema.get("properties", {}).items()
        }

        implementation = self.tool_implementations.get(definition_id)
        if implementation is None:
            def unavailable_implementation(**_: Any) -> Any:
                raise NotImplementedError(
                    f"Tool {definition_id} has no registered runtime implementation. "
                    "Register a trusted implementation before execution."
                )

            implementation = unavailable_implementation

        metadata = ToolMetadata(
            id=definition_id,
            name=data.get("name", definition_id),
            description=data.get("description", ""),
            version=metadata_dict.get("version", "1.0.0"),
            author=metadata_dict.get("author", "unknown"),
            category=metadata_dict.get("category", "general"),
            parameters=parameter_schemas,
            tags=metadata_dict.get("tags", []),
            pricing=metadata_dict.get("pricing"),
        )
        return Tool(
            id=definition_id,
            name=data.get("name", definition_id),
            description=data.get("description", ""),
            implementation=implementation,
            metadata=metadata,
            parameters=parameters_schema,
        )
    
    def list_tools(self) -> List[str]:
        """List all registered tool IDs with caching."""
        cache_key = "tools:list"
        
        # Try cache first
        cached_list = self.cache.get(cache_key)
        if cached_list:
            return cached_list
        
        # Load from filesystem
        tools_dir = self.base_path / "tools"
        tool_list = [f.stem for f in tools_dir.glob("*.json")]
        
        # Cache the list
        self.cache.set(cache_key, tool_list, ttl=self.cache_ttl)
        
        return tool_list
    
    # Workflow methods
    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow in the registry."""
        workflow_file = self.base_path / "workflows" / f"{workflow.id}.json"
        workflow_file.write_text(json.dumps(workflow.to_dict(), indent=2))
        
        # Invalidate cache
        self.cache.delete(f"workflow:{workflow.id}")
        self.cache.delete("workflows:list")
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get a workflow by ID with caching.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow instance or None
        """
        cache_key = f"workflow:{workflow_id}"
        
        # Try cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            data = cached_data
        else:
            workflow_file = self.base_path / "workflows" / f"{workflow_id}.json"
            if not workflow_file.exists():
                return None
            
            try:
                data = json.loads(workflow_file.read_text())
            except Exception:
                return None
        
        try:
            
            # Reconstruct workflow steps
            from agent_factory.workflows.model import WorkflowStep, Trigger, TriggerType, Condition
            
            steps = []
            for step_data in data.get("steps", []):
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
            
            # Reconstruct triggers
            triggers = []
            for trigger_data in data.get("triggers", []):
                trigger = Trigger(
                    type=TriggerType(trigger_data.get("type", "manual")),
                    config=trigger_data.get("config", {}),
                    enabled=trigger_data.get("enabled", True),
                )
                triggers.append(trigger)
            
            # Reconstruct branching
            branching = {}
            if "branching" in data:
                for step_id, cond_data in data["branching"].items():
                    branching[step_id] = Condition(
                        expression=cond_data.get("expression", ""),
                        description=cond_data.get("description"),
                    )
            
            # Resolve the persisted agent references so a registry round-trip is
            # executable in the same way as the original workflow.
            agents_registry = {
                agent_id: agent
                for agent_id in {step.agent_id for step in steps if step.agent_id}
                if (agent := self.get_agent(agent_id)) is not None
            }
            workflow = Workflow(
                id=data.get("id", workflow_id),
                name=data.get("name", ""),
                steps=steps,
                triggers=triggers if triggers else None,
                branching=branching if branching else None,
                agents_registry=agents_registry,
            )
            
            # Cache the workflow data
            if cached_data is None:
                self.cache.set(cache_key, data, ttl=self.cache_ttl)
            
            return workflow
        except Exception as e:
            # Log error but don't fail completely
            import logging
            logging.warning(f"Failed to load workflow {workflow_id}: {e}")
            return None
    
    def list_workflows(self) -> List[str]:
        """List all registered workflow IDs with caching."""
        cache_key = "workflows:list"
        
        # Try cache first
        cached_list = self.cache.get(cache_key)
        if cached_list:
            return cached_list
        
        # Load from filesystem
        workflows_dir = self.base_path / "workflows"
        workflow_list = [f.stem for f in workflows_dir.glob("*.json")]
        
        # Cache the list
        self.cache.set(cache_key, workflow_list, ttl=self.cache_ttl)
        
        return workflow_list
    
    # Blueprint methods
    def register_blueprint(self, blueprint: Blueprint) -> None:
        """Register a blueprint in the registry."""
        blueprint_dir = self.base_path / "blueprints" / blueprint.id
        blueprint_dir.mkdir(parents=True, exist_ok=True)
        
        # Save blueprint.yaml
        (blueprint_dir / "blueprint.yaml").write_text(blueprint.to_yaml())
        
        # Invalidate cache
        self.cache.delete(f"blueprint:{blueprint.id}")
        self.cache.delete("blueprints:list")
    
    def get_blueprint(self, blueprint_id: str) -> Optional[Blueprint]:
        """Get a blueprint by ID with caching."""
        cache_key = f"blueprint:{blueprint_id}"
        
        # Try cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            # Reconstruct from cached YAML string
            import yaml
            pack_data = yaml.safe_load(cached_data)
            return Blueprint.from_dict(pack_data.get("blueprint", {}))
        
        blueprint_file = self.base_path / "blueprints" / blueprint_id / "blueprint.yaml"
        if not blueprint_file.exists():
            return None
        
        blueprint = Blueprint.from_yaml(str(blueprint_file))
        
        # Cache the blueprint YAML
        yaml_content = blueprint_file.read_text()
        self.cache.set(cache_key, yaml_content, ttl=self.cache_ttl)
        
        return blueprint
    
    def list_blueprints(self) -> List[str]:
        """List all registered blueprint IDs with caching."""
        cache_key = "blueprints:list"
        
        # Try cache first
        cached_list = self.cache.get(cache_key)
        if cached_list:
            return cached_list
        
        # Load from filesystem
        blueprints_dir = self.base_path / "blueprints"
        blueprint_list = [d.name for d in blueprints_dir.iterdir() if d.is_dir()]
        
        # Cache the list
        self.cache.set(cache_key, blueprint_list, ttl=self.cache_ttl)
        
        return blueprint_list
    
    def search(self, query: str, category: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Search registry for agents, tools, workflows, and blueprints.
        
        Args:
            query: Search query
            category: Optional category filter ("agent", "tool", "workflow", "blueprint")
            
        Returns:
            Dictionary with search results
        """
        results = {
            "agents": [],
            "tools": [],
            "workflows": [],
            "blueprints": [],
        }
        
        query_lower = query.lower()
        
        if not category or category == "agent":
            for agent_id in self.list_agents():
                agent = self.get_agent(agent_id)
                if agent and query_lower in agent.name.lower():
                    results["agents"].append(agent_id)
        
        if not category or category == "tool":
            for tool_id in self.list_tools():
                # Simplified search
                if query_lower in tool_id.lower():
                    results["tools"].append(tool_id)
        
        if not category or category == "workflow":
            for workflow_id in self.list_workflows():
                if query_lower in workflow_id.lower():
                    results["workflows"].append(workflow_id)
        
        if not category or category == "blueprint":
            for blueprint_id in self.list_blueprints():
                blueprint = self.get_blueprint(blueprint_id)
                if blueprint and query_lower in blueprint.name.lower():
                    results["blueprints"].append(blueprint_id)
        
        return results
