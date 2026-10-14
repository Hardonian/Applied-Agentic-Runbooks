"""
Tool interface, registry, decorators, and JIT synthesizer.
"""

from agent_factory.tools.base import Tool, ToolMetadata, ParameterSchema
from agent_factory.tools.decorator import function_tool
from agent_factory.tools.jit_synthesizer import (
    JITToolSynthesizer,
    ToolSynthesisSpec,
    DynamicSynthesizedTool,
    ToolSecurityViolation,
)

__all__ = [
    "Tool",
    "ToolMetadata",
    "ParameterSchema",
    "function_tool",
    "JITToolSynthesizer",
    "ToolSynthesisSpec",
    "DynamicSynthesizedTool",
    "ToolSecurityViolation",
]
