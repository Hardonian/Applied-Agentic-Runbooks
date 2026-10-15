"""Tests for SelfHealingAgentExecutor and resilience engine."""

from unittest.mock import Mock

import pytest

from agent_factory.agents.agent import Agent, AgentResult, AgentStatus
from agent_factory.runtime.self_healing import (
    FailureCategory,
    RecoveryStrategy,
    SelfHealingAgentExecutor,
)
from agent_factory.security.circuit_breaker import CircuitBreaker


@pytest.mark.unit
def test_self_healing_successful_execution_first_attempt():
    """Verify clean execution succeeds on first attempt without healing."""
    mock_agent = Mock(spec=Agent)
    mock_agent.id = "clean-agent"
    mock_agent.run.return_value = AgentResult(
        output="Deterministic output",
        status=AgentStatus.COMPLETED,
        tokens_used=150,
        execution_time=0.1,
    )

    executor = SelfHealingAgentExecutor(agent=mock_agent, max_retries=3)
    result = executor.execute("Perform task")

    assert result.status == AgentStatus.COMPLETED
    assert result.output == "Deterministic output"
    assert result.healed is False
    assert result.total_attempts == 1
    assert len(result.healing_history) == 0


@pytest.mark.unit
def test_self_healing_recovers_after_transient_error():
    """Verify executor recovers when first attempt fails and second attempt succeeds."""
    mock_agent = Mock(spec=Agent)
    mock_agent.id = "recovering-agent"

    # 1st call fails, 2nd call succeeds
    mock_agent.run.side_effect = [
        AgentResult(
            output="",
            status=AgentStatus.ERROR,
            error="Rate limit exceeded: 429 Too Many Requests",
            tokens_used=50,
        ),
        AgentResult(
            output="Recovered response after throttle",
            status=AgentStatus.COMPLETED,
            tokens_used=120,
        ),
    ]

    executor = SelfHealingAgentExecutor(
        agent=mock_agent, max_retries=3, initial_backoff=0.01
    )
    result = executor.execute("Process data")

    assert result.status == AgentStatus.COMPLETED
    assert result.healed is True
    assert result.total_attempts == 2
    assert len(result.healing_history) == 1
    assert result.healing_history[0].category == FailureCategory.RATE_LIMIT
    assert result.healing_history[0].strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF
    assert result.output == "Recovered response after throttle"


@pytest.mark.unit
def test_self_healing_schema_correction():
    """Verify executor enforces schema validation and repairs output format."""
    mock_agent = Mock(spec=Agent)
    mock_agent.id = "json-agent"

    # 1st call returns invalid json, 2nd call returns valid json matching schema
    mock_agent.run.side_effect = [
        AgentResult(
            output="Here is the result: not json",
            status=AgentStatus.COMPLETED,
            tokens_used=30,
        ),
        AgentResult(
            output='{"decision": "approved", "score": 95}',
            status=AgentStatus.COMPLETED,
            tokens_used=60,
        ),
    ]

    schema = {
        "type": "object",
        "required": ["decision", "score"],
    }

    executor = SelfHealingAgentExecutor(
        agent=mock_agent, max_retries=3, initial_backoff=0.01
    )
    result = executor.execute("Evaluate candidate", expected_schema=schema)

    assert result.status == AgentStatus.COMPLETED
    assert result.healed is True
    assert result.total_attempts == 2
    assert result.healing_history[0].strategy == RecoveryStrategy.SCHEMA_CORRECTION
    assert "decision" in result.output


@pytest.mark.unit
def test_self_healing_circuit_breaker_halts():
    """Verify executor halts when circuit breaker threshold is tripped."""
    mock_agent = Mock(spec=Agent)
    mock_agent.id = "failing-agent"
    mock_agent.run.return_value = AgentResult(
        output="",
        status=AgentStatus.ERROR,
        error="Connection refused by backend",
    )

    from agent_factory.security.circuit_breaker import CircuitBreakerConfig
    cb = CircuitBreaker("test_cb", CircuitBreakerConfig(failure_threshold=2, timeout=60.0))
    executor = SelfHealingAgentExecutor(
        agent=mock_agent, max_retries=4, circuit_breaker=cb, initial_backoff=0.01
    )

    # First execution trips 2 failures
    res1 = executor.execute("Run query")
    assert res1.status == AgentStatus.ERROR

    # Once circuit is open, subsequent execution is blocked immediately
    res2 = executor.execute("Run query again")
    assert res2.status == AgentStatus.ERROR
    assert "circuit breaker" in res2.error.lower()
