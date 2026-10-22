"""
AutoTune - Automatically optimize agent configurations.
"""

from pathlib import Path
from typing import Any

import yaml

from agent_factory.agents.agent import AgentConfig
from agent_factory.eval.model import BenchmarkSuite
from agent_factory.eval.runner import BenchmarkRunner
from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.runtime.engine import RuntimeEngine


def autotune_agent(
    agent_id: str,
    suite: BenchmarkSuite,
    config_space: dict[str, list[Any]] | None = None,
    output_path: str | None = None,
    runtime: RuntimeEngine | None = None,
) -> AgentConfig:
    """
    Automatically tune agent configuration.

    Args:
        agent_id: Agent ID to tune
        suite: Benchmark suite for evaluation
        config_space: Configuration space to search (optional)
        output_path: Path to save tuned config (optional)
        runtime: Optional runtime engine (will create default if not provided)

    Returns:
        Optimized AgentConfig
    """
    if config_space is None:
        config_space = {
            "temperature": [0.0, 0.3, 0.7, 1.0],
            "max_tokens": [500, 1000, 2000],
        }

    # Create runtime if not provided
    if runtime is None:
        runtime = RuntimeEngine()

    # Load agent
    agent = runtime.agents_registry.get(agent_id)
    if not agent:
        registry = LocalRegistry()
        agent = registry.get_agent(agent_id)
        if agent:
            runtime.register_agent(agent)
        else:
            raise ValueError(f"Agent not found: {agent_id}")

    runner = BenchmarkRunner(runtime=runtime)

    # Try different configurations
    best_config = None
    best_score = float("-inf")

    # Simple grid search (would use more sophisticated optimization in production)
    for temp in config_space.get("temperature", [0.7]):
        for max_tokens in config_space.get("max_tokens", [2000]):
            # Create config override
            config_override = {
                "temperature": temp,
                "max_tokens": max_tokens,
            }

            # Temporarily update agent config
            original_config = agent.config
            try:
                # Create new config with overrides
                if original_config:
                    new_config = AgentConfig(
                        temperature=config_override.get("temperature", original_config.temperature),
                        max_tokens=config_override.get("max_tokens", original_config.max_tokens),
                        timeout=config_override.get("timeout", original_config.timeout),
                        retry_attempts=config_override.get(
                            "retry_attempts", original_config.retry_attempts
                        ),
                    )
                else:
                    new_config = AgentConfig(
                        temperature=config_override.get("temperature", 0.7),
                        max_tokens=config_override.get("max_tokens", 2000),
                    )

                agent.config = new_config

                # Run benchmark with this config
                results = runner.run_benchmark(agent_id, suite)

                # Calculate score from results
                # Score = weighted combination of accuracy, latency, and cost
                score = _calculate_score(results)

                if score > best_score:
                    best_score = score
                    best_config = new_config
            finally:
                # Restore original config
                agent.config = original_config

    # Save if output path provided
    if output_path and best_config:
        _save_tuned_config(agent_id, best_config, output_path)

    return best_config or AgentConfig()


def _calculate_score(results: list[Any]) -> float:
    """
    Calculate optimization score from benchmark results.

    Higher is better. Combines accuracy, latency, and cost.
    """
    if not results:
        return 0.0

    # Calculate average metrics
    total_accuracy = 0.0
    total_latency = 0.0
    total_cost = 0.0
    successful = 0

    for result in results:
        if result.success:
            successful += 1
            if result.accuracy is not None:
                total_accuracy += result.accuracy
            total_latency += result.latency
            total_cost += result.cost_estimate

    if successful == 0:
        return 0.0

    avg_accuracy = total_accuracy / successful if successful > 0 else 0.0
    avg_latency = total_latency / len(results) if results else 0.0
    avg_cost = total_cost / len(results) if results else 0.0

    # Normalize latency (lower is better, so invert)
    # Assume max acceptable latency is 10 seconds
    latency_score = max(0.0, 1.0 - (avg_latency / 10.0))

    # Normalize cost (lower is better, so invert)
    # Assume max acceptable cost is $1.00
    cost_score = max(0.0, 1.0 - (avg_cost / 1.0))

    # Weighted combination: accuracy is most important
    score = (0.5 * avg_accuracy) + (0.3 * latency_score) + (0.2 * cost_score)

    return score


def _save_tuned_config(agent_id: str, config: AgentConfig, output_path: str) -> None:
    """Save tuned configuration to YAML file."""
    config_dict = {
        "agent": {
            "id": agent_id,
            "config": {
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "timeout": config.timeout,
                "retry_attempts": config.retry_attempts,
            },
            "metadata": {
                "tuned": True,
            },
        }
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False)


# Placeholder for AgentConfig (would be imported from agents.config)
class AgentConfig:
    """Placeholder for agent config."""

    def __init__(
        self,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 30,
        retry_attempts: int = 3,
    ):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retry_attempts = retry_attempts
