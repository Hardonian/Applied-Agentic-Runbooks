"""
Multi-agent orchestration executor.
"""

import json
import time
import uuid
from typing import Any

from agent_factory.orchestration.graph import AgentGraph
from agent_factory.orchestration.router import AgentRouter
from agent_factory.promptlog import SQLiteStorage
from agent_factory.promptlog.model import Run as RunModel


class OrchestrationExecutor:
    """Execute multi-agent orchestration flows."""
    
    def __init__(self, storage: SQLiteStorage | None = None):
        """
        Initialize executor.
        
        Args:
            storage: Optional prompt log storage
        """
        self.router = AgentRouter()
        self.storage = storage
    
    def execute(
        self,
        graph: AgentGraph,
        inputs: dict[str, Any],
        max_steps: int = 10,
    ) -> dict[str, Any]:
        """
        Execute multi-agent flow.
        
        Args:
            graph: Agent graph
            inputs: Initial inputs
            max_steps: Maximum number of routing steps
        
        Returns:
            Final outputs
        """
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")

        current_agent_id = graph.entry_point
        current_message = dict(inputs)
        step_count = 0
        steps: list[dict[str, Any]] = []
        
        while current_agent_id and step_count < max_steps:
            # Get current agent
            node = graph.get_node(current_agent_id)
            if not node:
                return {
                    "output": None,
                    "status": "error",
                    "error": f"Orchestration node not found: {current_agent_id}",
                    "steps": steps,
                }
            
            # Agent.run accepts text while routing carries structured context.
            # Preserve a caller-provided input_text when available and encode
            # all other context deterministically for the executing agent.
            input_text = current_message.get("input_text")
            if not isinstance(input_text, str):
                input_text = json.dumps(current_message, sort_keys=True, default=str)
            started_at = time.perf_counter()
            agent_result = node.agent.run(input_text, context=current_message)
            result = {
                "output": agent_result.output,
                "status": agent_result.status.value,
                "error": agent_result.error,
                "tokens_used": agent_result.tokens_used,
                "execution_time": agent_result.execution_time,
                "agent_id": current_agent_id,
            }
            steps.append(result)
            
            # Log execution
            if self.storage:
                run = RunModel(
                    run_id=f"orchestration-{uuid.uuid4()}",
                    agent_id=current_agent_id,
                    inputs=current_message,
                    outputs=result,
                    status="success" if result["status"] == "completed" else "error",
                    execution_time=time.perf_counter() - started_at,
                    tokens_used=int(result["tokens_used"] or 0),
                )
                self.storage.save_run(run)

            if result["status"] == "error":
                return {**result, "steps": steps}
            
            # Route to next agent
            next_agent_id = self.router.route(result, current_agent_id, graph)
            
            if not next_agent_id:
                return {**result, "steps": steps}
            
            current_agent_id = next_agent_id
            current_message = result
            step_count += 1
        
        return {
            "output": current_message.get("output"),
            "status": "error",
            "error": f"Maximum orchestration steps exceeded ({max_steps})",
            "steps": steps,
        }
