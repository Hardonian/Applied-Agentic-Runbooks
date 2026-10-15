"""
Tool decorator - Convert Python functions to Tools.
"""

from collections.abc import Callable

from agent_factory.tools.base import Tool


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
        >>> # calculate is now a Tool instance that can be called directly
        >>> result = calculate(expression="2 + 2")
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
        
        return tool
    
    return decorator
