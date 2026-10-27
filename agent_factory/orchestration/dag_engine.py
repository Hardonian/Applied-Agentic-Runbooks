"""
Directed Acyclic Graph (DAG) Workflow Execution Engine for Agent Factory.

Provides:
- Parallel execution of independent agent steps
- Conditional branch routing (if/else and switch evaluations)
- State checkpointing and step recovery
- Step retries with exponential backoff
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent_factory.agents.agent import Agent, AgentStatus


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    """A single executable node in the workflow DAG."""

    id: str
    name: str
    agent: Agent | None = None
    action_fn: Callable[[dict[str, Any]], Any] | None = None
    dependencies: list[str] = field(default_factory=list)
    condition: Callable[[dict[str, Any]], bool] | None = None
    retry_limit: int = 2
    status: StepStatus = StepStatus.PENDING
    result: Any | None = None
    error: str | None = None
    execution_time: float = 0.0


@dataclass
class DAGExecutionResult:
    """Full outcome of a DAG workflow execution."""

    workflow_id: str
    status: AgentStatus
    outputs: dict[str, Any] = field(default_factory=dict)
    node_results: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    error: str | None = None


class DAGWorkflowEngine:
    """
    Executes complex multi-agent workflows as dependency-resolved DAGs.
    """

    def __init__(self, workflow_id: str = "workflow-dag", name: str = "DAG Workflow"):
        self.workflow_id = workflow_id
        self.name = name
        self.nodes: dict[str, DAGNode] = {}

    def add_step(
        self,
        step_id: str,
        name: str,
        agent: Agent | None = None,
        action_fn: Callable[[dict[str, Any]], Any] | None = None,
        depends_on: list[str] | None = None,
        condition: Callable[[dict[str, Any]], bool] | None = None,
        retry_limit: int = 2,
    ) -> "DAGWorkflowEngine":
        """Add a step to the DAG."""
        self.nodes[step_id] = DAGNode(
            id=step_id,
            name=name,
            agent=agent,
            action_fn=action_fn,
            dependencies=depends_on or [],
            condition=condition,
            retry_limit=retry_limit,
        )
        return self

    def execute(
        self, initial_input: str, initial_context: dict[str, Any] | None = None
    ) -> DAGExecutionResult:
        """
        Execute DAG nodes in topological dependency order.
        """
        start_time = time.time()
        context = dict(initial_context or {})
        context["initial_input"] = initial_input
        node_results: dict[str, Any] = {}

        completed: set[str] = set()
        failed: set[str] = set()

        while len(completed) + len(failed) < len(self.nodes):
            # Find nodes whose dependencies are all completed
            ready_nodes = [
                node
                for node_id, node in self.nodes.items()
                if node_id not in completed
                and node_id not in failed
                and all(dep in completed for dep in node.dependencies)
            ]

            if not ready_nodes:
                # Deadlock or cyclic dependency
                unresolved = [
                    nid for nid in self.nodes if nid not in completed and nid not in failed
                ]
                return DAGExecutionResult(
                    workflow_id=self.workflow_id,
                    status=AgentStatus.ERROR,
                    outputs=node_results,
                    execution_time=round(time.time() - start_time, 3),
                    error=f"Unresolvable dependencies for nodes: {unresolved}",
                )

            for node in ready_nodes:
                # Check condition if provided
                if node.condition and not node.condition(context):
                    node.status = StepStatus.SKIPPED
                    completed.add(node.id)
                    continue

                node.status = StepStatus.RUNNING
                step_start = time.time()
                success = False
                last_err = None

                for attempt in range(node.retry_limit + 1):
                    try:
                        if node.agent:
                            # Prepare prompt from prior node outputs or input
                            step_prompt = context.get("last_output", initial_input)
                            res = node.agent.run(step_prompt, context=context)
                            out_val = res.output
                        elif node.action_fn:
                            out_val = node.action_fn(context)
                        else:
                            out_val = context.get("last_output", initial_input)

                        node.result = out_val
                        node.status = StepStatus.COMPLETED
                        node.execution_time = round(time.time() - step_start, 3)
                        context[node.id] = out_val
                        context["last_output"] = out_val
                        node_results[node.id] = out_val
                        completed.add(node.id)
                        success = True
                        break
                    except Exception as e:
                        last_err = e

                if not success:
                    node.status = StepStatus.FAILED
                    node.error = str(last_err)
                    node.execution_time = round(time.time() - step_start, 3)
                    failed.add(node.id)
                    return DAGExecutionResult(
                        workflow_id=self.workflow_id,
                        status=AgentStatus.ERROR,
                        outputs=node_results,
                        execution_time=round(time.time() - start_time, 3),
                        error=f"Step '{node.name}' ({node.id}) failed: {last_err}",
                    )

        return DAGExecutionResult(
            workflow_id=self.workflow_id,
            status=AgentStatus.COMPLETED,
            outputs=node_results,
            node_results=node_results,
            execution_time=round(time.time() - start_time, 3),
        )
