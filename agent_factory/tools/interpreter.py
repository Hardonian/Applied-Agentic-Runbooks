"""
Secure Sandboxed Python AST Code Interpreter for Agent Factory.

Provides:
- AST syntax parsing and security validation
- Dangerous builtins and module blocking (os.system, subprocess, eval, file overrides)
- Standard library safe execution sandbox (math, datetime, json, re, statistics)
- Stdout/stderr capture and return value serialization
"""

import ast
import datetime
import io
import json
import math
import re
import statistics
import sys
from typing import Any

from agent_factory.tools.base import Tool, ToolResult

# Forbidden AST node types and names
FORBIDDEN_NAMES = {
    "eval", "exec", "compile", "__import__", "open", "file",
    "input", "raw_input", "reload", "globals", "locals", "vars",
    "subprocess", "shutil", "socket", "requests", "urllib", "os"
}

def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name in {"math", "json", "re", "datetime", "statistics"}:
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Import of module '{name}' is forbidden in sandbox.")


SAFE_GLOBALS: dict[str, Any] = {
    "__builtins__": {
        "__import__": _safe_import,
        "abs": abs,
        "all": all,
        "any": any,
        "bin": bin,
        "bool": bool,
        "dict": dict,
        "divmod": divmod,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "format": format,
        "frozenset": frozenset,
        "hex": hex,
        "int": int,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "iter": iter,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "next": next,
        "oct": oct,
        "ord": ord,
        "pow": pow,
        "print": print,
        "range": range,
        "repr": repr,
        "reversed": reversed,
        "round": round,
        "set": set,
        "slice": slice,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "type": type,
        "zip": zip,
        "True": True,
        "False": False,
        "None": None,
    },
    "math": math,
    "json": json,
    "re": re,
    "datetime": datetime,
    "statistics": statistics,
}


class CodeSecurityValidator(ast.NodeVisitor):
    """AST validator detecting unsafe calls, imports, and access patterns."""

    def __init__(self):
        self.errors: list[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name not in {"math", "json", "re", "datetime", "statistics"}:
                self.errors.append(f"Import of module '{alias.name}' is forbidden in sandbox.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module not in {"math", "json", "re", "datetime", "statistics"}:
            self.errors.append(f"Import from module '{node.module}' is forbidden in sandbox.")
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in FORBIDDEN_NAMES:
            self.errors.append(f"Access to forbidden identifier '{node.id}' is blocked.")
        self.generic_visit(node)


class SandboxedPythonInterpreter:
    """
    Executes Python snippets safely within an isolated scope.
    """

    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds

    def execute(self, code: str) -> dict[str, Any]:
        """
        Execute code safely and capture output and return variables.
        """
        # Step 1: Parse and validate AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "output": "",
                "error": f"Syntax Error: {e}",
            }

        validator = CodeSecurityValidator()
        validator.visit(tree)
        if validator.errors:
            return {
                "success": False,
                "output": "",
                "error": f"Security Violation: {'; '.join(validator.errors)}",
            }

        # Step 2: Execute with stdout/stderr redirection
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr

        local_scope: dict[str, Any] = {}
        global_scope = SAFE_GLOBALS.copy()

        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # If last statement is an expression, evaluate it
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                last_expr = tree.body.pop()
                exec(compile(tree, "<sandbox>", "exec"), global_scope, local_scope)
                eval_val = eval(compile(ast.Expression(last_expr.value), "<sandbox>", "eval"), global_scope, local_scope)
                if eval_val is not None:
                    print(eval_val)
            else:
                exec(compile(tree, "<sandbox>", "exec"), global_scope, local_scope)

            out = stdout_capture.getvalue()
            err = stderr_capture.getvalue()
            return {
                "success": True,
                "output": out if out else (err if err else "[Execution finished with no output]"),
                "error": err if err else None,
                "locals": {k: str(v) for k, v in local_scope.items() if not k.startswith("__")},
            }
        except Exception as e:
            return {
                "success": False,
                "output": stdout_capture.getvalue(),
                "error": f"{type(e).__name__}: {e!s}",
            }
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def create_code_interpreter_tool() -> Tool:
    """Factory creating a standard Agent Factory Code Interpreter Tool."""
    interpreter = SandboxedPythonInterpreter()

    def run_code(code: str) -> ToolResult:
        res = interpreter.execute(code)
        return ToolResult(
            output=res["output"] if res["success"] else f"Execution Error: {res['error']}",
            success=res["success"],
            error=res.get("error"),
        )

    return Tool(
        id="sandboxed_code_interpreter",
        name="python_interpreter",
        description="Executes Python code in a secure sandbox with data analytics and math libraries.",
        parameters={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute safely"
                }
            },
            "required": ["code"]
        },
        func=run_code,
    )
