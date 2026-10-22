"""
Tool base class - Core primitive for tools that agents can use.
"""

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agent_factory.core.exceptions import ToolExecutionError, ToolValidationError


@dataclass
class ParameterSchema:
    """Schema for a tool parameter."""

    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None


@dataclass
class ToolMetadata:
    """Metadata for a tool."""

    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "unknown"
    category: str = "general"
    parameters: dict[str, ParameterSchema] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    pricing: dict[str, Any] | None = None


@dataclass
class ToolResult:
    """Standard result structure returned from a tool execution."""

    output: Any
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Tool:
    """
    Abstract base class for tools that agents can use.

    Tools are functions that agents can call to perform actions.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        implementation: Callable | None = None,
        metadata: ToolMetadata | None = None,
        func: Callable | None = None,
        parameters: dict[str, Any] | None = None,
    ):
        """
        Initialize a Tool.

        Args:
            id: Unique identifier
            name: Human-readable name
            description: Description of what the tool does
            implementation: Callable that implements the tool logic (or func)
            metadata: Optional metadata
            func: Alias for implementation
            parameters: Optional pre-defined JSON schema for parameters
        """
        self.id = id
        self.name = name
        self.description = description
        self._implementation = implementation or func or (lambda **kwargs: str(kwargs))
        self.parameters = parameters
        self.metadata = metadata or ToolMetadata(
            id=id,
            name=name,
            description=description,
        )
        self._schema = parameters or self._infer_schema()

    def _infer_schema(self) -> dict[str, Any]:
        """Infer JSON schema from function signature."""
        sig = inspect.signature(self._implementation)
        parameters = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = self._python_type_to_json_type(param.annotation)
            param_schema = {
                "type": param_type,
                "description": param_name,
            }

            if param.default != inspect.Parameter.empty:
                param_schema["default"] = param.default
            else:
                required.append(param_name)

            parameters[param_name] = param_schema

        return {
            "type": "object",
            "properties": parameters,
            "required": required,
        }

    @staticmethod
    def _python_type_to_json_type(python_type: Any) -> str:
        """Convert Python type to JSON schema type."""
        type_map = {
            str: "string",
            int: "number",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        if python_type in type_map:
            return type_map[python_type]

        # Handle Optional types
        origin = getattr(python_type, "__origin__", None)
        if origin is type(None) or (
            hasattr(python_type, "__args__") and type(None) in python_type.__args__
        ):
            return "string"  # Default

        return "string"  # Default fallback

    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        # Validate parameters
        self.validate(**kwargs)

        # Execute implementation
        try:
            return self._implementation(**kwargs)
        except (ToolExecutionError, ToolValidationError, FileNotFoundError, ValueError):
            # Declared tool-interface exceptions pass through unchanged so
            # callers can distinguish security rejections from failures.
            raise
        except Exception as e:
            raise ToolExecutionError(f"Tool {self.id} execution failed: {str(e)}") from e

    def __call__(self, *args, **kwargs) -> Any:
        """
        Make tool callable directly.

        Args:
            *args: Positional arguments (will be converted to kwargs based on signature)
            **kwargs: Keyword arguments

        Returns:
            Tool execution result
        """
        # If args provided, try to map them to function signature
        if args:
            import inspect

            sig = inspect.signature(self._implementation)
            param_names = list(sig.parameters.keys())
            for i, arg in enumerate(args):
                if i < len(param_names):
                    kwargs[param_names[i]] = arg

        return self.execute(**kwargs)

    def validate(self, **kwargs) -> bool:
        """
        Validate tool parameters.

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if valid

        Raises:
            ToolValidationError: If validation fails
        """
        required = self._schema.get("required", [])

        for param in required:
            if param not in kwargs:
                raise ToolValidationError(f"Missing required parameter: {param}")

        return True

    def get_schema(self) -> dict[str, Any]:
        """
        Get JSON schema for the tool.

        Returns:
            JSON schema dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parameters": self._schema,
            "metadata": {
                "version": self.metadata.version,
                "author": self.metadata.author,
                "category": self.metadata.category,
                "tags": self.metadata.tags,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize tool to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "schema": self.get_schema(),
            "metadata": {
                "version": self.metadata.version,
                "author": self.metadata.author,
                "category": self.metadata.category,
                "tags": self.metadata.tags,
            },
        }
