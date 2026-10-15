"""
Core module - Legacy imports for backward compatibility.
"""

# Import exceptions first to avoid circular imports
# These don't depend on anything else in core, so safe to import immediately
from agent_factory.core.exceptions import (
    AgentError,
    AgentExecutionError,
    AgentFactoryError,
    AgentNotFoundError,
    BlueprintError,
    BlueprintNotFoundError,
    BlueprintValidationError,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolValidationError,
    WorkflowError,
    WorkflowExecutionError,
    WorkflowNotFoundError,
)

# Import guardrails (doesn't depend on agents/tools)
from agent_factory.core.guardrails import Guardrail, GuardrailResult, Guardrails


# Use __getattr__ for lazy imports to avoid circular dependencies
# This allows "from agent_factory.core import Agent" to work without
# triggering circular imports during module initialization
def __getattr__(name: str):
    """Lazy import for Agent, Tool, Workflow classes to avoid circular imports."""
    if name in ("Agent", "AgentConfig", "AgentResult", "AgentStatus", "Handoff"):
        from agent_factory.agents.agent import Agent, AgentConfig, AgentResult, AgentStatus, Handoff
        if name == "Agent":
            return Agent
        elif name == "AgentConfig":
            return AgentConfig
        elif name == "AgentResult":
            return AgentResult
        elif name == "AgentStatus":
            return AgentStatus
        elif name == "Handoff":
            return Handoff
    elif name == "Tool":
        from agent_factory.core.tool import Tool
        return Tool
    elif name == "function_tool":
        from agent_factory.tools.decorator import function_tool
        return function_tool
    elif name in ("MemoryStore", "SQLiteMemoryStore"):
        from agent_factory.runtime.memory import MemoryStore, SQLiteMemoryStore
        if name == "MemoryStore":
            return MemoryStore
        elif name == "SQLiteMemoryStore":
            return SQLiteMemoryStore
    elif name in ("Workflow", "WorkflowStep", "WorkflowResult", "Trigger", "TriggerType", "Condition"):
        from agent_factory.core.workflow import (
            Condition,
            Trigger,
            TriggerType,
            Workflow,
            WorkflowResult,
            WorkflowStep,
        )
        if name == "Workflow":
            return Workflow
        elif name == "WorkflowStep":
            return WorkflowStep
        elif name == "WorkflowResult":
            return WorkflowResult
        elif name == "Trigger":
            return Trigger
        elif name == "TriggerType":
            return TriggerType
        elif name == "Condition":
            return Condition
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Agents
    "Agent",
    "AgentConfig",
    "AgentError",
    "AgentExecutionError",
    # Exceptions
    "AgentFactoryError",
    "AgentNotFoundError",
    "AgentResult",
    "AgentStatus",
    "BlueprintError",
    "BlueprintNotFoundError",
    "BlueprintValidationError",
    "Condition",
    "Guardrail",
    "GuardrailResult",
    # Guardrails
    "Guardrails",
    "Handoff",
    # Memory
    "MemoryStore",
    "SQLiteMemoryStore",
    # Tools
    "Tool",
    "ToolError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ToolValidationError",
    "Trigger",
    "TriggerType",
    # Workflows
    "Workflow",
    "WorkflowError",
    "WorkflowExecutionError",
    "WorkflowNotFoundError",
    "WorkflowResult",
    "WorkflowStep",
    "function_tool",
]
