"""
OpenAI Assistants & OpenAPI Specification Exporter for Agent Factory.

Generates:
- OpenAI Assistants API JSON manifests
- OpenAPI 3.1 REST API specifications for agents
"""

from typing import Any

from agent_factory.agents.agent import Agent


class OpenAISpecExporter:
    """
    Exports Agent Factory agents to OpenAI Assistants API and OpenAPI 3.1 specs.
    """

    @staticmethod
    def export_assistant_json(agent: Agent) -> dict[str, Any]:
        """Generate OpenAI Assistants API v2 creation payload."""
        tools_spec = []
        for t in agent.tools:
            tools_spec.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": getattr(
                            t,
                            "parameters",
                            {
                                "type": "object",
                                "properties": {},
                            },
                        ),
                    },
                }
            )

        return {
            "name": agent.name,
            "instructions": agent.instructions,
            "model": agent.model,
            "tools": tools_spec,
            "metadata": {
                "agent_factory_id": agent.id,
                "exported_by": "AgentFactory-v1.0",
            },
        }

    @staticmethod
    def export_openapi_schema(agent: Agent) -> dict[str, Any]:
        """Generate OpenAPI 3.1 schema definition for the agent microservice."""
        return {
            "openapi": "3.1.0",
            "info": {
                "title": f"{agent.name} API",
                "version": "1.0.0",
                "description": f"Autonomous API interface for {agent.name}.",
            },
            "paths": {
                f"/agents/{agent.id}/run": {
                    "post": {
                        "summary": f"Execute {agent.name}",
                        "operationId": f"run_{agent.id.replace('-', '_')}",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "input": {
                                                "type": "string",
                                                "description": "Prompt or task",
                                            },
                                            "session_id": {
                                                "type": "string",
                                                "description": "Memory session key",
                                            },
                                            "context": {
                                                "type": "object",
                                                "description": "Runtime context payload",
                                            },
                                        },
                                        "required": ["input"],
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "Successful execution",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "output": {"type": "string"},
                                                "status": {"type": "string"},
                                                "execution_time": {"type": "number"},
                                                "tokens_used": {"type": "integer"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
        }
