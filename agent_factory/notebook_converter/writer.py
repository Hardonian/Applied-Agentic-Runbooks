"""
Write agents, tools, and workflows to files.
"""

from pathlib import Path
from typing import Any

import yaml


class AgentWriter:
    """Write agent configurations to YAML files."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.agents_dir = output_dir / "agents"
        self.agents_dir.mkdir(parents=True, exist_ok=True)

    def write(self, agent_id: str, agent_def: dict[str, Any]) -> Path:
        """
        Write agent configuration to YAML file.

        Args:
            agent_id: Agent identifier
            agent_def: Agent definition dictionary

        Returns:
            Path to written file
        """
        config = {
            "agent": {
                "id": agent_id,
                "name": agent_def.get("name", agent_id.replace("-", " ").title()),
                "instructions": agent_def.get("instructions", ""),
                "model": agent_def.get("model", "gpt-4o"),
                "config": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
                "tools": agent_def.get("tools", []),
                "metadata": {
                    "source": "notebook",
                },
            }
        }

        file_path = self.agents_dir / f"{agent_id}_config.yaml"
        with open(file_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        return file_path


class ToolWriter:
    """Write tool implementations to Python files."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.tools_dir = output_dir / "tools"
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.source_code_cache: dict[str, str] = {}  # Cache source code for AST reconstruction

    def write(
        self,
        tool_id: str,
        tool_def: dict[str, Any],
        source_code: str | None = None,
        ast_node: Any | None = None,
    ) -> Path:
        """
        Write tool implementation to Python file.

        Args:
            tool_id: Tool identifier
            tool_def: Tool definition dictionary
            source_code: Optional source code string (for AST reconstruction)
            ast_node: Optional AST node (for code extraction)

        Returns:
            Path to written file
        """
        code = tool_def.get("code", "")

        # If code exists (from ast.unparse), use it
        if code:
            # Ensure it's properly formatted
            if not code.strip().startswith("@function_tool"):
                # Add decorator if missing
                if "@function_tool" not in code:
                    code = "@function_tool\n" + code
        elif ast_node and source_code:
            # Extract function code from AST and source
            code = self._extract_function_code(ast_node, source_code)
        else:
            # Generate template as fallback
            code = self._generate_tool_template(tool_id, tool_def)

        # Ensure imports
        if "from agent_factory.tools import function_tool" not in code:
            code = "from agent_factory.tools import function_tool\n\n" + code

        file_path = self.tools_dir / f"{tool_id}.py"
        with open(file_path, "w") as f:
            f.write(f'"""Tool: {tool_id} - Extracted from notebook"""\n\n')
            f.write(code)
            if not code.endswith("\n"):
                f.write("\n")

        return file_path

    def _extract_function_code(self, func_node: Any, source_code: str) -> str:
        """
        Extract function code from AST node and source code.

        Uses line numbers to extract the exact function body.
        """
        import ast

        try:
            # Try to use ast.unparse if available (Python 3.9+)
            if hasattr(ast, "unparse"):
                return ast.unparse(func_node)
        except (
            Exception
        ):  # nosec B110 -- ast.unparse fallback path -- guarded by hasattr above, returns None to fall back to source text
            pass

        # Fallback: extract using line numbers
        try:
            lines = source_code.split("\n")
            start_line = func_node.lineno - 1  # AST uses 1-based, list uses 0-based
            end_line = func_node.end_lineno if hasattr(func_node, "end_lineno") else len(lines)

            # Extract function lines
            func_lines = lines[start_line:end_line]

            # Find the actual function start (account for decorators)
            decorator_count = len(func_node.decorator_list)
            if decorator_count > 0:
                # Find the first decorator line
                first_decorator_line = func_node.decorator_list[0].lineno - 1
                func_lines = lines[first_decorator_line:end_line]

            return "\n".join(func_lines)
        except Exception:
            # If extraction fails, return template
            return ""

    def _generate_tool_template(self, tool_id: str, tool_def: dict[str, Any]) -> str:
        """Generate a tool template if code is missing."""
        params = tool_def.get("parameters", [])
        param_str = ", ".join(
            f"{p['name']}: {p.get('type', 'str')}"
            + (" = None" if not p.get("required", True) else "")
            for p in params
        )

        return f"""@function_tool
def {tool_id}({param_str}):
    \"\"\"{tool_def.get('description', 'Tool extracted from notebook')}\"\"\"
    # TODO: Implement tool logic
    pass
"""


class WorkflowWriter:
    """Write workflow definitions to YAML files."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.workflows_dir = output_dir / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def write(self, workflow_id: str, workflow_def: dict[str, Any]) -> Path:
        """
        Write workflow definition to YAML file.

        Args:
            workflow_id: Workflow identifier
            workflow_def: Workflow definition dictionary

        Returns:
            Path to written file
        """
        config = {
            "workflow": {
                "id": workflow_id,
                "name": workflow_def.get("name", workflow_id.replace("-", " ").title()),
                "steps": workflow_def.get("steps", []),
                "metadata": {
                    "source": "notebook",
                },
            }
        }

        file_path = self.workflows_dir / f"{workflow_id}_workflow.yaml"
        with open(file_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        return file_path
