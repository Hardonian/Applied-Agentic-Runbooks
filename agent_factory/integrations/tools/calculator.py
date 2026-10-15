"""Calculator tool for mathematical operations."""

import math

from agent_factory.tools.decorator import function_tool
from agent_factory.utils.safe_evaluator import safe_evaluate


@function_tool(
    name="calculator",
    description="Perform mathematical calculations"
)
def calculator(expression: str) -> float:
    """
    Calculate a mathematical expression safely.
    
    Supports basic arithmetic, comparisons, and safe math functions.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Calculation result
        
    Raises:
        ValueError: If expression is invalid or unsafe
    """
    # Add math functions to context
    math_functions = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    
    try:
        result = safe_evaluate(expression, context=math_functions)
        return float(result)
    except ValueError as e:
        raise ValueError(f"Invalid expression: {e!s}")
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {e!s}")


# The decorator returns a Tool instance, so calculator is already a Tool
calculator_tool = calculator
