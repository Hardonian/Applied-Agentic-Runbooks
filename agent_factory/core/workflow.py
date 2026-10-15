"""
Workflow orchestration for multi-agent systems.
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
                else:
                    return WorkflowResult(
                        success=False,
                        error=f"Workflow step not found: {start_step}",
                    )
            
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
                        # Condition not met, skip remaining steps or branch to alternative path
                        # For now, stop execution if condition not met
                        # In production, would support alternative branch paths
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
        """
        Map workflow context to agent input.
        
        Args:
            mapping: Input mapping dictionary
            context: Workflow context
            
        Returns:
            Mapped input string
        """
        # Simple mapping - in production, would support expressions like "$trigger.query"
        if not mapping:
            # Default: use first context value as input
            return str(next(iter(context.values())) if context else "")
        
        # Build input from mapped values
        inputs = []
        for key, value_path in mapping.items():
            # Resolve value_path from context (simplified)
            value = self._resolve_path(value_path, context)
            inputs.append(f"{key}: {value}")
        
        return "\n".join(inputs)
    
    def _map_outputs(self, mapping: dict[str, str], output: str) -> dict[str, Any]:
        """
        Map agent output to workflow context.
        
        Args:
            mapping: Output mapping dictionary
            output: Agent output string
            
        Returns:
            Mapped output dictionary
        """
        result = {}
        
        if not mapping:
            # Default: store output as "output"
            result["output"] = output
        else:
            for key in mapping:
                # For now, simple mapping
                result[key] = output
        
        return result
    
    def _resolve_path(self, path: str, context: dict[str, Any]) -> Any:
        """
        Resolve a path expression in context.
        
        Args:
            path: Path expression (e.g., "$steps.search.output")
            context: Workflow context dictionary
            
        Returns:
            Resolved value or None
        """
        # Simple implementation - in production, would support "$steps.search.output"
        if path.startswith("$"):
            # Remove $ and resolve
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
        
        # Safe operators for evaluation
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
                # Resolve from context
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
            # Parse expression
            tree = ast.parse(expression, mode='eval')
            result = eval_node(tree.body)
            return bool(result)
        except Exception:
            # Fallback to simple string replacement and safe evaluation
            for key, value in context.items():
                expression = expression.replace(f"${key}", str(value))
            try:
                # Use safe evaluator instead of eval
                from agent_factory.utils.safe_evaluator import safe_evaluate
                result = safe_evaluate(expression, context={})
                return bool(result)
            except Exception:
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
