"""
Prompt log data models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Run:
    """
    Single agent/workflow execution record.

    Example:
        >>> run = Run(
        ...     run_id="run-123",
        ...     agent_id="research-assistant",
        ...     inputs={"query": "Python async"},
        ...     outputs={"result": "..."},
        ...     status="success",
        ...     execution_time=2.5,
        ... )
    """

    run_id: str
    agent_id: str | None = None
    workflow_id: str | None = None
    step_id: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    status: str = "success"  # "success", "error", "timeout"
    execution_time: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptLogEntry:
    """
    Detailed prompt/response log entry.

    Example:
        >>> entry = PromptLogEntry(
        ...     run_id="run-123",
        ...     step=1,
        ...     prompt="What is Python async?",
        ...     response="Python async allows...",
        ...     tool_calls=[],
        ... )
    """

    run_id: str
    step: int
    prompt: str
    response: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
