"""
Universal Interoperability & Multi-Framework Export Suite for Agent Factory.

Supports 1-click export to:
- LangGraph (StateGraph DAGs)
- CrewAI (Agents, Tasks, Crews)
- AutoGen / AG2 (ConversableAgent, GroupChat)
- LlamaIndex (Event-driven Workflows)
- Docker & OCI Microservices (Container bundles)
- OpenAI Assistants & OpenAPI 3.1 specs
"""

from agent_factory.agents.agent import Agent
from agent_factory.interop.autogen_exporter import AutoGenExporter
from agent_factory.interop.crewai_exporter import CrewAIExporter
from agent_factory.interop.docker_packager import DockerPackager
from agent_factory.interop.langgraph_exporter import LangGraphExporter
from agent_factory.interop.llamaindex_exporter import LlamaIndexExporter
from agent_factory.interop.openai_spec import OpenAISpecExporter


def export_agent(agent: Agent, target_framework: str = "langgraph") -> str:
    """
    Universal agent exporter function.
    
    Args:
        agent: Agent Factory Agent instance
        target_framework: 'langgraph', 'crewai', 'autogen', 'llamaindex', 'docker', 'openapi', 'openai_assistant'
        
    Returns:
        Code string or serialized specification
    """
    target = target_framework.lower().strip()
    if target == "langgraph":
        return LangGraphExporter.export_agent(agent)
    elif target == "crewai":
        return CrewAIExporter.export_agent(agent)
    elif target in {"autogen", "ag2"}:
        return AutoGenExporter.export_agent(agent)
    elif target == "llamaindex":
        return LlamaIndexExporter.export_agent(agent)
    elif target == "docker":
        return DockerPackager.generate_server_entrypoint(agent)
    elif target in {"openai", "openai_assistant"}:
        import json
        return json.dumps(OpenAISpecExporter.export_assistant_json(agent), indent=2)
    elif target == "openapi":
        import json
        return json.dumps(OpenAISpecExporter.export_openapi_schema(agent), indent=2)
    else:
        raise ValueError(f"Unsupported export target framework: '{target_framework}'. Supported: langgraph, crewai, autogen, llamaindex, docker, openai, openapi")


__all__ = [
    "AutoGenExporter",
    "CrewAIExporter",
    "DockerPackager",
    "LangGraphExporter",
    "LlamaIndexExporter",
    "OpenAISpecExporter",
    "export_agent",
]
