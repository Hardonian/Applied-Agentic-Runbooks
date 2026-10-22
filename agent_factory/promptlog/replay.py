"""
Replay agent runs with different configurations.
"""

import uuid
from typing import TYPE_CHECKING, Any, Optional

from agent_factory.promptlog.model import Run
from agent_factory.promptlog.storage import PromptLogStorage

if TYPE_CHECKING:
    from agent_factory.runtime.engine import RuntimeEngine


def replay_run(
    run_id: str,
    storage: PromptLogStorage,
    agent_config_override: dict[str, Any] | None = None,
    runtime: Optional["RuntimeEngine"] = None,
) -> Run:
    """
    Replay a run with optional configuration overrides.

    Args:
        run_id: ID of run to replay
        storage: Storage backend
        agent_config_override: Optional config overrides
        runtime: Optional runtime engine (will create default if not provided)

    Returns:
        New Run with replayed execution
    """
    # Get original run
    original_run = storage.get_run(run_id)
    if not original_run:
        raise ValueError(f"Run not found: {run_id}")

    from agent_factory.agents.agent import AgentConfig
    from agent_factory.registry.local_registry import LocalRegistry
    from agent_factory.runtime.engine import RuntimeEngine

    # Create runtime engine if not provided
    if runtime is None:
        runtime = RuntimeEngine(prompt_log_storage=storage)

    # Get agent ID
    agent_id = original_run.agent_id
    if not agent_id:
        raise ValueError("Original run has no agent_id")

    # Load agent from registry or runtime
    agent = runtime.agents_registry.get(agent_id)
    if not agent:
        # Try loading from registry
        registry = LocalRegistry()
        agent = registry.get_agent(agent_id)
        if agent:
            runtime.register_agent(agent)
        else:
            raise ValueError(f"Agent not found: {agent_id}")

    # Apply config overrides if provided
    if agent_config_override:
        if agent.config:
            # Update existing config
            for key, value in agent_config_override.items():
                if hasattr(agent.config, key):
                    setattr(agent.config, key, value)
        else:
            # Create new config
            agent.config = AgentConfig(**agent_config_override)

    # Extract input text from original run
    input_text = original_run.inputs.get("input", "")
    if not input_text and isinstance(original_run.inputs, dict):
        # Try to find input in various formats
        input_text = original_run.inputs.get("input_text", "")
        if not input_text:
            # Use first string value as input
            for value in original_run.inputs.values():
                if isinstance(value, str):
                    input_text = value
                    break

    if not input_text:
        raise ValueError("Could not extract input text from original run")

    # Replay the run via runtime engine
    try:
        execution_id = runtime.run_agent(
            agent_id=agent_id,
            input_text=input_text,
            session_id=f"{run_id}-replay",
            context=original_run.inputs,
        )

        # Get execution result
        execution = runtime.get_execution(execution_id)
        if not execution:
            raise ValueError("Execution not found after replay")

        # Extract result
        result = execution.result
        if result:
            output = result.output if hasattr(result, "output") else str(result)
            execution_time = result.execution_time if hasattr(result, "execution_time") else 0.0
            tokens_used = result.tokens_used if hasattr(result, "tokens_used") else 0
        else:
            output = ""
            execution_time = 0.0
            tokens_used = 0

        # Create new run record
        new_run_id = f"{run_id}-replay-{uuid.uuid4().hex[:8]}"
        new_run = Run(
            run_id=new_run_id,
            agent_id=agent_id,
            workflow_id=original_run.workflow_id,
            inputs=original_run.inputs,
            outputs={"output": output},
            status="success" if execution.status == "completed" else "error",
            execution_time=execution_time,
            tokens_used=tokens_used,
            cost_estimate=original_run.cost_estimate,
            metadata={
                "replayed_from": run_id,
                "config_override": agent_config_override or {},
                "execution_id": execution_id,
            },
        )

        # Save new run
        storage.save_run(new_run)
        return new_run

    except Exception as e:
        # Create error run
        new_run_id = f"{run_id}-replay-{uuid.uuid4().hex[:8]}"
        new_run = Run(
            run_id=new_run_id,
            agent_id=agent_id,
            workflow_id=original_run.workflow_id,
            inputs=original_run.inputs,
            outputs={"error": str(e)},
            status="error",
            execution_time=0.0,
            tokens_used=0,
            cost_estimate=0.0,
            metadata={
                "replayed_from": run_id,
                "config_override": agent_config_override or {},
                "error": str(e),
            },
        )
        storage.save_run(new_run)
        raise
