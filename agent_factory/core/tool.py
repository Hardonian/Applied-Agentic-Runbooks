"""
Tool interface and registry for Agent Factory Platform.
"""

import inspect
from abc import ABC
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


class Tool(ABC):
    """
    Abstract base class for tools that agents can use.
    
    Tools are functions that agents can call to perform actions.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        implementation: Callable,
        metadata: ToolMetadata | None = None,
    ):
        """
        Initialize a Tool.
        
        Args:
            id: Unique identifier
            name: Human-readable name
            description: Description of what the tool does
            implementation: Callable that implements the tool logic
            metadata: Optional metadata
        """
        self.id = id
        self.name = name
        self.description = description
        self._implementation = implementation
        self.metadata = metadata or ToolMetadata(
            id=id,
            name=name,
            description=description,
        )
        self._schema = self._infer_schema()
    
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
        if origin is type(None) or (hasattr(python_type, "__args__") and type(None) in python_type.__args__):
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
        except Exception as e:
            raise ToolExecutionError(f"Tool {self.id} execution failed: {e!s}")
    
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


def function_tool(
    name: str | None = None,
    description: str | None = None,
    **tool_kwargs
):
    """
    Decorator to convert a Python function into a Tool.
    
    Example:
        >>> @function_tool(name="calculate", description="Calculate math expressions")
        ... def calculate(expression: str) -> float:
        ...     return eval(expression)
        >>> tool = calculate  # Now it's a Tool instance
    """
    def decorator(func: Callable) -> Tool:
        tool_id = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {func.__name__}"
        
        # Create Tool instance
        tool = Tool(
            id=tool_id,
            name=tool_id.replace("_", " ").title(),
            description=tool_description,
            implementation=func,
        )
        
        # Attach tool attributes to function
        func.tool = tool
        func.id = tool_id
        
        return tool
    
    return decorator
