"""Exception hierarchy for Agent Factory Platform."""


class AgentFactoryError(Exception):
    """Base exception for all Agent Factory errors."""

    pass


class AgentError(AgentFactoryError):
    """Base exception for agent-related errors."""

    pass


class AgentNotFoundError(AgentError):
    """Raised when an agent is not found."""

    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    pass


class ToolError(AgentFactoryError):
    """Base exception for tool-related errors."""

    pass


class ToolNotFoundError(ToolError):
    """Raised when a tool is not found."""

    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""

    pass


class ToolValidationError(ToolError):
    """Raised when tool validation fails."""

    pass


class WorkflowError(AgentFactoryError):
    """Base exception for workflow-related errors."""

    pass


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow is not found."""

    pass


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails."""

    pass


class BlueprintError(AgentFactoryError):
    """Base exception for blueprint-related errors."""

    pass


class BlueprintNotFoundError(BlueprintError):
    """Raised when a blueprint is not found."""

    pass


class BlueprintValidationError(BlueprintError):
    """Raised when blueprint validation fails."""

    pass


class RegistryError(AgentFactoryError):
    """Base exception for registry-related errors."""

    pass


class RegistryNotFoundError(RegistryError):
    """Raised when a registry resource is not found."""

    pass


class DatabaseError(AgentFactoryError):
    """Base exception for database-related errors."""

    pass


class ConfigurationError(AgentFactoryError):
    """Raised when configuration is invalid."""

    pass
