"""
Tool interface, registry, decorators, and JIT synthesizer.
"""

from agent_factory.tools.base import ParameterSchema, Tool, ToolMetadata
from agent_factory.tools.decorator import function_tool
from agent_factory.tools.jit_synthesizer import (
    DynamicSynthesizedTool,
    JITToolSynthesizer,
    ToolSecurityViolation,
    ToolSynthesisSpec,
)

__all__ = [
    "DynamicSynthesizedTool",
    "JITToolSynthesizer",
    "ParameterSchema",
    "Tool",
    "ToolMetadata",
    "ToolSecurityViolation",
    "ToolSynthesisSpec",
    "function_tool",
]
