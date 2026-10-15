"""Tests for Tool class."""

import pytest

from agent_factory.tools.base import Tool, ToolValidationError
from agent_factory.tools.decorator import function_tool


@pytest.mark.unit
def test_tool_creation():
    """Test creating a tool."""
    def dummy_function(x: str) -> str:
        return f"Result: {x}"
    
    tool = Tool(
        id="test-tool",
        name="Test Tool",
        description="A test tool",
        implementation=dummy_function,
    )
    
    assert tool.id == "test-tool"
    assert tool.name == "Test Tool"
    assert tool.description == "A test tool"


@pytest.mark.unit
def test_tool_execution():
    """Test tool execution."""
    def add(a: int, b: int) -> int:
        return a + b
    
    tool = Tool(
        id="add",
        name="Add",
        description="Add two numbers",
        implementation=add,
    )
    
    result = tool.execute(a=5, b=3)
    assert result == 8
    
    # Test callable interface
    result2 = tool(a=5, b=3)
    assert result2 == 8


@pytest.mark.unit
def test_tool_validation():
    """Test tool parameter validation."""
    def add(a: int, b: int) -> int:
        return a + b
    
    tool = Tool(
        id="add",
        name="Add",
        description="Add two numbers",
        implementation=add,
    )
    
    # Valid call
    tool.validate(a=5, b=3)
    
    # Missing required parameter
    with pytest.raises(ToolValidationError):
        tool.validate(a=5)


@pytest.mark.unit
def test_function_tool_decorator():
    """Test function_tool decorator."""
    @function_tool(name="test_tool", description="A test tool")
    def test_function(x: str) -> str:
        return f"Processed: {x}"
    
    # The decorator returns a Tool instance directly
    assert isinstance(test_function, Tool)
    assert test_function.id == "test_tool"


@pytest.mark.unit
def test_tool_schema():
    """Test tool schema generation."""
    def example_function(name: str, age: int = 25) -> str:
        return f"{name} is {age}"
    
    tool = Tool(
        id="example",
        name="Example",
        description="Example tool",
        implementation=example_function,
    )
    
    schema = tool.get_schema()
    assert "parameters" in schema
    assert "properties" in schema["parameters"]
