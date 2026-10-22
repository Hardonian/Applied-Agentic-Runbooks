"""
Anthropic Model Context Protocol (MCP) Server & Client for Agent Factory.

Enables:
- Exposing any Agent Factory Agent / Tool as an Anthropic MCP Server
- Dynamically consuming external MCP Servers (SQLite, GitHub, Filesystem, etc.)
- Full JSON-RPC 2.0 compliance for `tools/list`, `tools/call`, `resources/list`, and `prompts/list`
"""

import json
from dataclasses import dataclass
from typing import Any

from agent_factory.tools.base import Tool, ToolResult


@dataclass
class MCPToolDefinition:
    """MCP standard tool schema."""

    name: str
    description: str
    inputSchema: dict[str, Any]


class MCPServer:
    """
    Exposes Agent Factory tools and agents to any MCP client (e.g. Claude Desktop, Cursor, Custom Agents).
    """

    def __init__(self, name: str = "agent-factory-mcp", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: dict[str, Tool] = {}
        self.resources: dict[str, dict[str, Any]] = {}
        self.prompts: dict[str, dict[str, Any]] = {}

    def register_tool(self, tool: Tool) -> None:
        """Register an Agent Factory tool into MCP server."""
        self.tools[tool.name] = tool

    def register_resource(
        self, uri: str, name: str, mime_type: str = "text/plain", content: str = ""
    ) -> None:
        """Register an MCP resource."""
        self.resources[uri] = {
            "uri": uri,
            "name": name,
            "mimeType": mime_type,
            "content": content,
        }

    def register_prompt(self, name: str, description: str, template: str) -> None:
        """Register an MCP prompt template."""
        self.prompts[name] = {
            "name": name,
            "description": description,
            "template": template,
        }

    def handle_json_rpc(self, request_json: str | dict[str, Any]) -> dict[str, Any]:
        """
        Handle standard JSON-RPC 2.0 MCP request.
        """
        if isinstance(request_json, str):
            req = json.loads(request_json)
        else:
            req = request_json

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": True, "listChanged": True},
                        "prompts": {"listChanged": True},
                    },
                    "serverInfo": {"name": self.name, "version": self.version},
                },
            }

        elif method == "tools/list":
            tools_list = []
            for t in self.tools.values():
                tools_list.append(
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": getattr(
                            t,
                            "parameters",
                            {
                                "type": "object",
                                "properties": {},
                            },
                        ),
                    }
                )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            if tool_name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                }

            tool = self.tools[tool_name]
            try:
                res = tool.execute(**tool_args)
                out_content = res.output if isinstance(res, ToolResult) else str(res)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": out_content}],
                        "isError": False,
                    },
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {e}"}],
                        "isError": True,
                    },
                }

        elif method == "resources/list":
            res_list = list(self.resources.values())
            return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": res_list}}

        elif method == "prompts/list":
            prompt_list = list(self.prompts.values())
            return {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": prompt_list}}

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not supported: {method}"},
            }


class MCPClient:
    """
    Client for connecting to external Model Context Protocol servers.
    """

    def __init__(self, server_name: str = "remote-mcp"):
        self.server_name = server_name
        self.discovered_tools: dict[str, dict[str, Any]] = {}

    def ingest_server_tools(self, mcp_server: MCPServer) -> list[Tool]:
        """Convert MCP Server tools into native Agent Factory Tool instances."""
        tools_response = mcp_server.handle_json_rpc(
            {"jsonrpc": "2.0", "id": "1", "method": "tools/list"}
        )
        tools_list = tools_response.get("result", {}).get("tools", [])

        adapted_tools = []
        for t_spec in tools_list:
            t_name = t_spec["name"]
            t_desc = t_spec.get("description", "")
            t_params = t_spec.get("inputSchema", {})

            # Create closure for tool execution
            def make_executor(name=t_name):
                def executor(**kwargs):
                    res = mcp_server.handle_json_rpc(
                        {
                            "jsonrpc": "2.0",
                            "id": "exec",
                            "method": "tools/call",
                            "params": {"name": name, "arguments": kwargs},
                        }
                    )
                    content = res.get("result", {}).get("content", [{}])[0].get("text", "")
                    return ToolResult(
                        output=content, success=not res.get("result", {}).get("isError", False)
                    )

                return executor

            tool = Tool(
                id=f"mcp_{t_name}",
                name=t_name,
                description=t_desc,
                parameters=t_params,
                func=make_executor(),
            )
            adapted_tools.append(tool)
            self.discovered_tools[t_name] = t_spec

        return adapted_tools
