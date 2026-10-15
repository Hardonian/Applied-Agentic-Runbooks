"""
Infer UI schema from agent/tool definitions.
"""

from typing import Any

from agent_factory.agents.agent import Agent


def infer_ui_schema(agent: Agent) -> dict[str, Any]:
    """
    Infer UI schema from agent definition.
    
    Args:
        agent: Agent to infer schema for
    
    Returns:
        UI schema dictionary
    """
    schema: dict[str, Any] = {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "inputs": [],
        "outputs": [],
    }
    
    # Infer input schema from agent tools
    input_schema = _infer_input_schema(agent)
    schema["inputs"] = input_schema
    
    # Infer output schema from agent response format
    output_schema = _infer_output_schema(agent)
    schema["outputs"] = output_schema
    
    return schema


def _infer_input_schema(agent: Agent) -> list[dict[str, Any]]:
    """
    Infer input schema from agent tools.
    
    Collects all parameters from all tools and creates a unified input schema.
    """
    inputs = []
    seen_params = set()
    
    # Collect parameters from all tools
    for tool in agent.tools:
        if hasattr(tool, "get_schema"):
            tool_schema = tool.get_schema()
            params = tool_schema.get("parameters", {}).get("properties", {})
            required = tool_schema.get("parameters", {}).get("required", [])
            
            for param_name, param_def in params.items():
                # Avoid duplicates
                if param_name in seen_params:
                    continue
                seen_params.add(param_name)
                
                input_field = {
                    "name": param_name,
                    "type": param_def.get("type", "string"),
                    "description": param_def.get("description", param_name),
                    "required": param_name in required,
                    "default": param_def.get("default"),
                }
                
                # Add enum if present
                if "enum" in param_def:
                    input_field["enum"] = param_def["enum"]
                
                inputs.append(input_field)
    
    # If no tool parameters, create a default text input
    if not inputs:
        inputs.append({
            "name": "input",
            "type": "string",
            "description": "Input text",
            "required": True,
        })
    
    return inputs


def _infer_output_schema(agent: Agent) -> list[dict[str, Any]]:
    """
    Infer output schema from agent response format.
    
    Agents typically return text output, but we can infer structure
    from tool return types or agent metadata.
    """
    outputs = []
    
    # Default: agents return text output
    outputs.append({
        "name": "output",
        "type": "string",
        "description": "Agent response",
    })
    
    # If agent has specific output format metadata, use it
    if hasattr(agent, "metadata") and agent.metadata:
        output_format = agent.metadata.get("output_format")
        if output_format:
            if output_format == "json":
                outputs = [{
                    "name": "output",
                    "type": "object",
                    "description": "Structured JSON response",
                }]
            elif output_format == "list":
                outputs = [{
                    "name": "output",
                    "type": "array",
                    "description": "List response",
                }]
    
    return outputs
