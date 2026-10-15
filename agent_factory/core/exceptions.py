"""Exception hierarchy for Agent Factory Platform."""


class AgentFactoryError(Exception):
    """Base exception for all Agent Factory errors."""


class AgentError(AgentFactoryError):
    """Base exception for agent-related errors."""


class AgentNotFoundError(AgentError):
    """Raised when an agent is not found."""


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""


class ToolError(AgentFactoryError):
    """Base exception for tool-related errors."""


class ToolNotFoundError(ToolError):
    """Raised when a tool is not found."""


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""


class ToolValidationError(ToolError):
    """Raised when tool validation fails."""


class WorkflowError(AgentFactoryError):
    """Base exception for workflow-related errors."""


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow is not found."""


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails."""


class BlueprintError(AgentFactoryError):
    """Base exception for blueprint-related errors."""


class BlueprintNotFoundError(BlueprintError):
    """Raised when a blueprint is not found."""


class BlueprintValidationError(BlueprintError):
    """Raised when blueprint validation fails."""


class RegistryError(AgentFactoryError):
    """Base exception for registry-related errors."""


class RegistryNotFoundError(RegistryError):
    """Raised when a registry resource is not found."""


class DatabaseError(AgentFactoryError):
    """Base exception for database-related errors."""


class ConfigurationError(AgentFactoryError):
    """Raised when configuration is invalid."""
