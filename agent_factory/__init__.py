"""
Agent Factory Platform

A composable, extensible platform for building, deploying, and monetizing AI agents.
"""

__version__ = "1.0.0"

# Core primitives
from agent_factory.agents.agent import Agent, AgentConfig, AgentResult
from agent_factory.blueprints.model import Blueprint
from agent_factory.financial.token_goblin import TokenGoblinGovernor
from agent_factory.optimization.cascade_router import SpeculativeCascadeRouter
from agent_factory.orchestration.veridag import VeriDAGEngine
from agent_factory.reasoning.mcts import SpeculativeMCTSEngine
from agent_factory.security.mcpwall import MCPWall
from agent_factory.telemetry.pcap import AgentPCAPTracer
from agent_factory.tools.base import Tool
from agent_factory.tools.decorator import function_tool
from agent_factory.tools.jit_synthesizer import JITToolSynthesizer
from agent_factory.workflows.model import Workflow

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentPCAPTracer",
    "AgentResult",
    "Blueprint",
    "JITToolSynthesizer",
    "MCPWall",
    "SpeculativeCascadeRouter",
    "SpeculativeMCTSEngine",
    "TokenGoblinGovernor",
    "Tool",
    "VeriDAGEngine",
    "Workflow",
    "function_tool",
]
