"""
Safe expression evaluator for mathematical and logical expressions.

Replaces unsafe eval() usage with AST-based evaluation.
"""

import ast
import operator
from typing import Any, Callable, cast


class SafeEvaluator:
    """
    Safe evaluator for mathematical and logical expressions.
    
    Supports:
    - Basic arithmetic (+, -, *, /, %, **)
    - Comparisons (==, !=, <, >, <=, >=)
    - Logical operations (and, or, not)
    - Math functions (abs, round, min, max, sum)
    - Constants (pi, e)
    
    Example:
        >>> evaluator = SafeEvaluator()
        >>> result = evaluator.evaluate("2 + 2 * 3")
        8
        >>> result = evaluator.evaluate("abs(-5)")
        5
    """
    
    # Safe operators
    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
        ast.FloorDiv: operator.floordiv,
    }
    
    # Safe comparison operators
    _COMPARATORS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
    }
    
    # Safe unary operators
    _UNARY_OPERATORS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Not: operator.not_,
        ast.Invert: operator.invert,
    }
    
    # Safe functions
    _SAFE_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
    }
    
    # Safe constants
    _SAFE_CONSTANTS = {
        "pi": 3.141592653589793,
        "e": 2.718281828459045,
    }
    
    def __init__(self, additional_functions: dict[str, Any] | None = None):
        """
        Initialize safe evaluator.
        
        Args:
            additional_functions: Optional dict of additional safe functions
        """
        self.functions: dict[str, Any] = {**self._SAFE_FUNCTIONS}
        if additional_functions:
            self.functions.update(additional_functions)
    
    def evaluate(self, expression: str, context: dict[str, Any] | None = None) -> Any:
        """
        Safely evaluate an expression.
        
        Args:
            expression: Expression string to evaluate
            context: Optional context dictionary for variables
            
        Returns:
            Evaluation result
            
        Raises:
            ValueError: If expression is invalid or unsafe
        """
        if not expression or not isinstance(expression, str):
            raise ValueError("Expression must be a non-empty string")
        
        # Parse expression
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")
        
        # Evaluate AST
        context = context or {}
        return self._eval_node(tree.body, context)
    
    def _eval_node(self, node: ast.AST, context: dict[str, Any]) -> Any:
        """Recursively evaluate AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        
        elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
            return node.s
        
        elif isinstance(node, ast.NameConstant):  # Python < 3.8 compatibility
            return node.value
        
        elif isinstance(node, ast.Name):
            # Check if it's a safe constant
            if node.id in self._SAFE_CONSTANTS:
                return self._SAFE_CONSTANTS[node.id]
            # Check context
            if node.id in context:
                return context[node.id]
            raise ValueError(f"Unknown variable or constant: {node.id}")
        
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op = self._OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            try:
                return op(left, right)
            except Exception as e:
                raise ValueError(f"Error evaluating binary operation: {e}")
        
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            unary_op = self._UNARY_OPERATORS.get(type(node.op))
            if unary_op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return cast(Callable[[Any], Any], unary_op)(operand)
        
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            result = True
            for cmp_op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)
                op_func = self._COMPARATORS.get(type(cmp_op))
                if op_func is None:
                    raise ValueError(f"Unsupported comparison operator: {type(cmp_op).__name__}")
                if not op_func(left, right):
                    result = False
                    break
                left = right
            return result
        
        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, context) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)
            else:
                raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")
        
        elif isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                # Handle math.sqrt, etc.
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "math":
                    func_name = node.func.attr
                elif (
                    isinstance(node.func.value, ast.Call)
                    and isinstance(node.func.value.func, ast.Name)
                ):
                    # Report the attempted inner callable without traversing
                    # or evaluating its arguments.  This keeps chained calls
                    # such as ``__import__(...).system(...)`` safely denied
                    # with the same allow-list contract as direct calls.
                    func_name = node.func.value.func.id
                else:
                    raise ValueError("Only math module functions are supported")
            else:
                raise ValueError("Invalid function call")
            
            if func_name not in self.functions:
                raise ValueError(f"Function '{func_name}' is not allowed")
            
            args = [self._eval_node(arg, context) for arg in node.args]
            kwargs = {}
            for keyword in node.keywords:
                if keyword.arg is None:
                    raise ValueError("**kwargs not supported")
                kwargs[keyword.arg] = self._eval_node(keyword.value, context)
            
            try:
                return self.functions[func_name](*args, **kwargs)
            except Exception as e:
                raise ValueError(f"Error calling function '{func_name}': {e}")
        
        elif isinstance(node, ast.List):
            return [self._eval_node(elem, context) for elem in node.elts]
        
        elif isinstance(node, ast.Dict):
            return {
                self._eval_node(k, context): self._eval_node(v, context)  # type: ignore[arg-type]
                for k, v in zip(node.keys, node.values)
            }
        
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elem, context) for elem in node.elts)
        
        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, context)
            if isinstance(node.slice, ast.Index):  # Python < 3.9
                index = self._eval_node(getattr(node.slice, "value", node.slice), context)
            else:
                index = self._eval_node(node.slice, context)
            try:
                return value[index]
            except Exception as e:
                raise ValueError(f"Error accessing subscript: {e}")
        
        else:
            raise ValueError(f"Unsupported AST node type: {type(node).__name__}")


# Global instance for convenience
_default_evaluator = SafeEvaluator()


def safe_evaluate(expression: str, context: dict[str, Any] | None = None) -> Any:
    """
    Convenience function for safe expression evaluation.
    
    Args:
        expression: Expression string to evaluate
        context: Optional context dictionary
        
    Returns:
        Evaluation result
        
    Raises:
        ValueError: If expression is invalid or unsafe
    """
    return _default_evaluator.evaluate(expression, context)
