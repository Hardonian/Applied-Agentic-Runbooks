"""
Evaluation data models.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Scenario:
    """
    Evaluation scenario.
    
    Example:
        >>> scenario = Scenario(
        ...     id="tip-calculation",
        ...     name="Tip Calculation",
        ...     inputs={"amount": 100, "tip_percent": 15},
        ...     expected_outputs={"result": 15.0},
        ... )
    """
    id: str
    name: str
    inputs: dict[str, Any]
    expected_outputs: dict[str, Any] | None = None
    expected_behavior: str | None = None  # Natural language description
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """
    Result of evaluating an agent on a scenario.
    
    Example:
        >>> result = EvaluationResult(
        ...     scenario_id="tip-calculation",
        ...     agent_id="calculator-agent",
        ...     success=True,
        ...     accuracy=1.0,
        ...     latency=0.5,
        ...     tokens_used=50,
        ...     cost_estimate=0.001,
        ... )
    """
    scenario_id: str
    agent_id: str
    success: bool
    accuracy: float | None = None  # 0.0 to 1.0, if expected_outputs provided
    latency: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    error: str | None = None
    output: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSuite:
    """
    Collection of evaluation scenarios.
    
    Example:
        >>> suite = BenchmarkSuite(
        ...     id="math-basics",
        ...     name="Basic Math Operations",
        ...     scenarios=[scenario1, scenario2],
        ...     metrics=["accuracy", "latency", "cost"],
        ... )
    """
    id: str
    name: str
    scenarios: list[Scenario]
    metrics: list[str] = field(default_factory=lambda: ["accuracy", "latency", "cost", "error_rate"])
    metadata: dict[str, Any] = field(default_factory=dict)
