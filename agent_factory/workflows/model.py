"""
Workflow model - Multi-step agent orchestration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TriggerType(str, Enum):
    """Types of workflow triggers."""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    EVENT = "event"
    MANUAL = "manual"


@dataclass
class Condition:
    """Condition for workflow branching."""
    expression: str  # e.g., "$steps.search.output.count > 0"
    description: str | None = None


@dataclass
class Trigger:
    """Workflow trigger definition."""
    type: TriggerType
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class WorkflowStep:
    """A step in a workflow."""
    id: str
    agent_id: str
    input_mapping: dict[str, str] = field(default_factory=dict)  # Maps workflow vars to agent inputs
    output_mapping: dict[str, str] = field(default_factory=dict)  # Maps agent outputs to workflow vars
    condition: Condition | None = None
    timeout: int = 30  # seconds
    retry_attempts: int = 3


@dataclass
class WorkflowResult:
    """Result from workflow execution."""
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    steps_executed: list[str] = field(default_factory=list)
    execution_time: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Workflow:
    """
    Workflow for orchestrating multiple agents.
    
    Example:
        >>> workflow = Workflow(
        ...     id="research-pipeline",
        ...     name="Research Pipeline",
        ...     steps=[
        ...         WorkflowStep(id="search", agent_id="research-searcher"),
        ...         WorkflowStep(id="analyze", agent_id="research-analyzer"),
        ...     ]
        ... )
        >>> result = workflow.execute({"query": "Python async"})
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        steps: list[WorkflowStep],
        triggers: list[Trigger] | None = None,
        branching: dict[str, Condition] | None = None,
        agents_registry: dict[str, Any] | None = None,
    ):
        """
        Initialize a Workflow.
        
        Args:
            id: Unique identifier
            name: Human-readable name
            steps: List of workflow steps
            triggers: Optional list of triggers
            branching: Optional branching conditions
            agents_registry: Registry of available agents
        """
        self.id = id
        self.name = name
        self.steps = steps
        self.triggers = triggers or []
        self.branching = branching or {}
        self.agents_registry = agents_registry or {}
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps.append(step)
    
    def add_trigger(self, trigger: Trigger) -> None:
        """Add a trigger to the workflow."""
        self.triggers.append(trigger)
    
    def execute(
        self,
        context: dict[str, Any],
        start_step: str | None = None,
    ) -> WorkflowResult:
        """
        Execute the workflow with given context.
        
        Args:
            context: Initial context dictionary
            start_step: Optional step ID to start from
            
        Returns:
            WorkflowResult with execution results
        """
        import time
        start_time = time.time()
        
        try:
            workflow_context = context.copy()
            steps_executed = []
            
            # Determine starting step
            start_index = 0
            if start_step:
                for i, step in enumerate(self.steps):
                    if step.id == start_step:
                        start_index = i
                        break
            
            # Execute steps sequentially
            for i, step in enumerate(self.steps[start_index:], start=start_index):
                # Check condition if present
                if step.condition:
                    if not self._evaluate_condition(step.condition, workflow_context):
                        continue  # Skip this step
                
                # Get agent
                agent = self.agents_registry.get(step.agent_id)
                if not agent:
                    return WorkflowResult(
                        success=False,
                        error=f"Agent not found: {step.agent_id}",
                    )
                
                # Map inputs
                agent_input = self._map_inputs(step.input_mapping, workflow_context)
                
                # Execute agent
                agent_result = agent.run(agent_input)
                
                if agent_result.status.value == "error":
                    return WorkflowResult(
                        success=False,
                        error=f"Step {step.id} failed: {agent_result.error}",
                        steps_executed=steps_executed,
                    )
                
                # Map outputs
                step_output = self._map_outputs(step.output_mapping, agent_result.output)
                workflow_context.update(step_output)
                workflow_context[f"steps.{step.id}.output"] = agent_result.output
                
                steps_executed.append(step.id)
                
                # Check branching
                if step.id in self.branching:
                    condition = self.branching[step.id]
                    if not self._evaluate_condition(condition, workflow_context):
                        break
            
            execution_time = time.time() - start_time
            
            return WorkflowResult(
                success=True,
                output=workflow_context,
                steps_executed=steps_executed,
                execution_time=execution_time,
            )
            
        except Exception as e:
            return WorkflowResult(
                success=False,
                error=str(e),
                steps_executed=steps_executed if 'steps_executed' in locals() else [],
            )
    
    def _map_inputs(self, mapping: dict[str, str], context: dict[str, Any]) -> str:
        """Map workflow context to agent input."""
        if not mapping:
            return str(next(iter(context.values())) if context else "")
        
        inputs = []
        for key, value_path in mapping.items():
            value = self._resolve_path(value_path, context)
            inputs.append(f"{key}: {value}")
        
        return "\n".join(inputs)
    
    def _map_outputs(self, mapping: dict[str, str], output: str) -> dict[str, Any]:
        """Map agent output to workflow context."""
        result = {}
        
        if not mapping:
            result["output"] = output
        else:
            for key in mapping:
                result[key] = output
        
        return result
    
    def _resolve_path(self, path: str, context: dict[str, Any]) -> Any:
        """Resolve a path expression in context."""
        if path.startswith("$"):
            path = path[1:]
            parts = path.split(".")
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        
        return context.get(path, path)
    
    def _evaluate_condition(self, condition: Condition, context: dict[str, Any]) -> bool:
        """Evaluate a condition expression."""
        import ast
        import operator
        
        expression = condition.expression
        
        safe_operators = {
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.And: lambda a, b: a and b,
            ast.Or: lambda a, b: a or b,
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }
        
        def eval_node(node):
            """Safely evaluate an AST node."""
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Name):
                path = node.id.split(".")
                value = context
                for part in path:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        return None
                return value
            elif isinstance(node, ast.BinOp):
                left = eval_node(node.left)
                right = eval_node(node.right)
                op = safe_operators.get(type(node.op))
                if op:
                    return op(left, right)
            elif isinstance(node, ast.Compare):
                left = eval_node(node.left)
                for op, right in zip(node.ops, node.comparators):
                    right_val = eval_node(right)
                    op_func = safe_operators.get(type(op))
                    if op_func:
                        if not op_func(left, right_val):
                            return False
                        left = right_val
                return True
            elif isinstance(node, ast.BoolOp):
                values = [eval_node(v) for v in node.values]
                op = safe_operators.get(type(node.op))
                if op:
                    result = values[0]
                    for val in values[1:]:
                        result = op(result, val)
                    return result
            
            return False
        
        try:
            # Use safe evaluator instead of eval
            from agent_factory.utils.safe_evaluator import safe_evaluate
            
            # Replace $variables with actual values
            processed_expression = expression
            import re
            
            # Replace $key or $key.path patterns
            for key in context:
                pattern = r'\$' + re.escape(key) + r'(?:\.\w+)*'
                def replace_match(match):
                    matched = match.group(0)
                    if '.' in matched:
                        var_name = matched.split('.')[0][1:]
                        path_parts = matched.split('.')[1:]
                        try:
                            val = context.get(var_name, {})
                            for part in path_parts:
                                if isinstance(val, dict):
                                    val = val.get(part)
                                else:
                                    return 'None'
                            return str(val)
                        except Exception:
                            return 'None'
                    else:
                        return str(context.get(key, 'None'))
                
                processed_expression = re.sub(pattern, replace_match, processed_expression)
            
            result = safe_evaluate(processed_expression, context=context)
            return bool(result)
        except Exception:
            # Fallback: return False if evaluation fails
            return False
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize workflow to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "steps": [
                {
                    "id": step.id,
                    "agent_id": step.agent_id,
                    "input_mapping": step.input_mapping,
                    "output_mapping": step.output_mapping,
                    "condition": {
                        "expression": step.condition.expression,
                        "description": step.condition.description,
                    } if step.condition else None,
                    "timeout": step.timeout,
                    "retry_attempts": step.retry_attempts,
                }
                for step in self.steps
            ],
            "triggers": [
                {
                    "type": trigger.type.value,
                    "config": trigger.config,
                    "enabled": trigger.enabled,
                }
                for trigger in self.triggers
            ],
            "branching": {
                k: {"expression": v.expression, "description": v.description}
                for k, v in self.branching.items()
            },
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        agents_registry: dict[str, Any] | None = None,
    ) -> "Workflow":
        """Recreate a workflow from the registry/API representation."""
        steps = []
        for step_data in data.get("steps", []):
            condition_data = step_data.get("condition")
            condition = (
                Condition(
                    expression=condition_data.get("expression", ""),
                    description=condition_data.get("description"),
                )
                if condition_data
                else None
            )
            steps.append(
                WorkflowStep(
                    id=step_data["id"],
                    agent_id=step_data["agent_id"],
                    input_mapping=step_data.get("input_mapping", {}),
                    output_mapping=step_data.get("output_mapping", {}),
                    condition=condition,
                    timeout=step_data.get("timeout", 30),
                    retry_attempts=step_data.get("retry_attempts", 3),
                )
            )

        triggers = [
            Trigger(
                type=TriggerType(trigger_data.get("type", TriggerType.MANUAL.value)),
                config=trigger_data.get("config", {}),
                enabled=trigger_data.get("enabled", True),
            )
            for trigger_data in data.get("triggers", [])
        ]
        branching = {
            step_id: Condition(
                expression=condition_data.get("expression", ""),
                description=condition_data.get("description"),
            )
            for step_id, condition_data in data.get("branching", {}).items()
        }
        return cls(
            id=data["id"],
            name=data["name"],
            steps=steps,
            triggers=triggers,
            branching=branching,
            agents_registry=agents_registry,
        )
