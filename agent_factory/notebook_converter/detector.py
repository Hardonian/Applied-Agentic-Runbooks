"""
Detect agents, tools, and workflows in notebook code.
"""

import ast
from typing import Any


class AgentDetector:
    """Detect Agent instances in notebook code."""
    
    def detect(self, notebook_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Detect agents in notebook cells.
        
        Looks for:
        - Agent(...) instantiation
        - AgentFactory.create_*() calls
        - Variables named *_agent that are Agent instances
        
        Returns:
            List of detected agent definitions
        """
        agents = []
        
        for cell in notebook_data.get("cells", []):
            source = cell.get("source", "")
            try:
                tree = ast.parse(source)
                visitor = AgentVisitor()
                visitor.visit(tree)
                agents.extend(visitor.agents)
            except SyntaxError:
                # Skip cells with syntax errors
                continue
        
        return agents


class ToolDetector:
    """Detect Tool definitions in notebook code."""
    
    def detect(self, notebook_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Detect tools in notebook cells.
        
        Looks for:
        - Functions decorated with @function_tool
        - Functions with clear docstrings
        
        Returns:
            List of detected tool definitions
        """
        tools = []
        
        for cell in notebook_data.get("cells", []):
            source = cell.get("source", "")
            try:
                tree = ast.parse(source)
                visitor = ToolVisitor()
                visitor.visit(tree)
                tools.extend(visitor.tools)
            except SyntaxError:
                continue
        
        return tools


class WorkflowDetector:
    """Detect Workflow definitions in notebook code."""
    
    def detect(self, notebook_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Detect workflows in notebook cells.
        
        Looks for:
        - Workflow(...) instantiation
        - Sequential agent calls
        - Crew(...) patterns
        
        Returns:
            List of detected workflow definitions
        """
        workflows = []
        
        for cell in notebook_data.get("cells", []):
            source = cell.get("source", "")
            try:
                tree = ast.parse(source)
                visitor = WorkflowVisitor()
                visitor.visit(tree)
                workflows.extend(visitor.workflows)
            except SyntaxError:
                continue
        
        return workflows


class AgentVisitor(ast.NodeVisitor):
    """AST visitor to detect Agent instances."""
    
    def __init__(self):
        self.agents = []
    
    def visit_Call(self, node: ast.Call):
        """Detect Agent(...) or AgentFactory.create_*() calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id == "Agent":
                # Agent(...) instantiation
                agent_def = self._extract_agent_from_call(node)
                if agent_def:
                    self.agents.append(agent_def)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "AgentFactory":
                if node.func.attr.startswith("create_"):
                    # AgentFactory.create_*()
                    agent_def = self._extract_agent_from_factory_call(node)
                    if agent_def:
                        self.agents.append(agent_def)
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Detect assignments like agent = Agent(...)."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.endswith("_agent"):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name) and node.value.func.id == "Agent":
                        agent_def = self._extract_agent_from_call(node.value)
                        if agent_def:
                            agent_def["id"] = target.id.replace("_agent", "")
                            self.agents.append(agent_def)
        
        self.generic_visit(node)
    
    def _extract_agent_from_call(self, node: ast.Call) -> dict[str, Any] | None:
        """Extract agent definition from Agent(...) call."""
        agent_def: dict[str, Any] = {
            "id": None,
            "name": None,
            "instructions": None,
            "model": "gpt-4o",
            "tools": [],
        }
        
        # Extract keyword arguments
        for keyword in node.keywords:
            if keyword.arg == "name":
                if isinstance(keyword.value, ast.Constant):
                    agent_def["name"] = keyword.value.value
            elif keyword.arg == "instructions":
                if isinstance(keyword.value, ast.Constant):
                    agent_def["instructions"] = keyword.value.value
            elif keyword.arg == "model":
                if isinstance(keyword.value, ast.Constant):
                    agent_def["model"] = keyword.value.value
            elif keyword.arg == "tools" and isinstance(keyword.value, ast.List):
                agent_def["tools"] = [self._extract_tool_name(elem) for elem in keyword.value.elts]
        
        # Extract positional arguments (if any)
        if node.args and isinstance(node.args[0], ast.Constant):
            agent_def["name"] = agent_def["name"] or node.args[0].value
        
        return agent_def if agent_def["name"] or agent_def["instructions"] else None
    
    def _extract_agent_from_factory_call(self, node: ast.Call) -> dict[str, Any] | None:
        """Extract agent definition from AgentFactory.create_*() call."""
        if not isinstance(node.func, ast.Attribute):
            return None
        agent_type = node.func.attr.replace("create_", "").replace("_", " ")
        agent_def = {
            "id": agent_type.replace(" ", "-"),
            "name": agent_type.title(),
            "instructions": f"Agent created from {agent_type} factory",
            "model": "gpt-4o",
            "tools": [],
        }
        return agent_def
    
    def _extract_tool_name(self, node: ast.AST) -> str:
        """Extract tool name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "unknown_tool"


class ToolVisitor(ast.NodeVisitor):
    """AST visitor to detect Tool definitions."""
    
    def __init__(self):
        self.tools = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Detect functions that might be tools."""
        # Check for @function_tool decorator
        has_decorator = any(
            isinstance(decorator, ast.Name) and decorator.id == "function_tool"
            or isinstance(decorator, ast.Attribute) and decorator.attr == "function_tool"
            for decorator in node.decorator_list
        )
        
        if has_decorator or self._looks_like_tool(node):
            tool_def = self._extract_tool_definition(node)
            if tool_def:
                self.tools.append(tool_def)
        
        self.generic_visit(node)
    
    def _looks_like_tool(self, node: ast.FunctionDef) -> bool:
        """Heuristic: does this function look like a tool?"""
        # Has docstring
        docstring = ast.get_docstring(node)
        has_docstring = docstring is not None and len(docstring) > 20
        
        # Has type hints
        has_type_hints = any(
            param.annotation != ast.Constant(None)
            for param in node.args.args
        )
        
        return has_docstring and has_type_hints
    
    def _extract_tool_definition(self, node: ast.FunctionDef) -> dict[str, Any] | None:
        """Extract tool definition from function."""
        docstring = ast.get_docstring(node) or ""
        
        tool_def = {
            "id": node.name,
            "name": node.name.replace("_", " ").title(),
            "description": docstring.split("\n")[0] if docstring else "",
            "code": ast.unparse(node) if hasattr(ast, "unparse") else "",
            "parameters": self._extract_parameters(node),
        }
        
        return tool_def
    
    def _extract_parameters(self, node: ast.FunctionDef) -> list[dict[str, Any]]:
        """Extract function parameters."""
        params: list[dict[str, Any]] = []
        num_defaults = len(node.args.defaults)
        num_args = len(node.args.args)
        default_offset = num_args - num_defaults
        
        for idx, param in enumerate(node.args.args):
            is_required = idx < default_offset
            param_def = {
                "name": param.arg,
                "type": self._extract_type(param.annotation),
                "required": is_required,
            }
            params.append(param_def)
        return params
    
    def _extract_type(self, annotation: ast.AST | None) -> str:
        """Extract type from annotation."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        return "str"


class WorkflowVisitor(ast.NodeVisitor):
    """AST visitor to detect Workflow definitions."""
    
    def __init__(self):
        self.workflows = []
    
    def visit_Call(self, node: ast.Call):
        """Detect Workflow(...) or Crew(...) calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id == "Workflow":
                workflow_def = self._extract_workflow_from_call(node)
                if workflow_def:
                    self.workflows.append(workflow_def)
            elif node.func.id == "Crew":
                workflow_def = self._extract_crew_workflow(node)
                if workflow_def:
                    self.workflows.append(workflow_def)
        
        self.generic_visit(node)
    
    def _extract_workflow_from_call(self, node: ast.Call) -> dict[str, Any] | None:
        """Extract workflow definition from Workflow(...) call."""
        workflow_def: dict[str, Any] = {
            "id": None,
            "name": None,
            "steps": [],
        }
        
        for keyword in node.keywords:
            if keyword.arg == "id":
                if isinstance(keyword.value, ast.Constant):
                    workflow_def["id"] = keyword.value.value
            elif keyword.arg == "name":
                if isinstance(keyword.value, ast.Constant):
                    workflow_def["name"] = keyword.value.value
            elif keyword.arg == "steps" and isinstance(keyword.value, ast.List):
                workflow_def["steps"] = [
                    self._extract_step(elem) for elem in keyword.value.elts
                ]
        
        return workflow_def if workflow_def["id"] or workflow_def["name"] else None
    
    def _extract_crew_workflow(self, node: ast.Call) -> dict[str, Any] | None:
        """Extract workflow from Crew(...) call."""
        return {
            "id": "crew-workflow",
            "name": "Crew Workflow",
            "steps": [],
        }
    
    def _extract_step(self, node: ast.AST) -> dict[str, Any]:
        """Extract workflow step from AST node."""
        return {
            "id": "step",
            "agent_id": "agent",
        }
