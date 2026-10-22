"""
Agent Factory Platform

A composable, extensible platform for building, deploying, and monetizing AI agents.
"""

__version__ = "0.1.0"

# Core primitives
from agent_factory.agents.agent import Agent, AgentConfig, AgentResult
from agent_factory.blueprints.model import Blueprint
from agent_factory.tools.base import Tool
from agent_factory.tools.decorator import function_tool
from agent_factory.workflows.model import Workflow

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentResult",
    "Tool",
    "function_tool",
    "Workflow",
    "Blueprint",
]
