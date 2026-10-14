"""
Self-Healing Autonomous Agent Execution Engine.

Provides automated error diagnosis, reflection-guided retry, fallback tool selection,
and resilience safeguards for mission-critical production agent deployments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_factory.agents.agent import Agent, AgentResult, AgentStatus
from agent_factory.security.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState

logger = logging.getLogger(__name__)


class FailureCategory(str, Enum):
    """Categorized root causes of agent execution failures."""
    TOOL_ERROR = "tool_error"
    RATE_LIMIT = "rate_limit"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT = "timeout"
    HALLUCINATION = "hallucination"
    CIRCUIT_OPEN = "circuit_open"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    """Applied resilience strategy for self-healing."""
    RETRY_WITH_REFLECTION = "retry_with_reflection"
    FALLBACK_TOOL = "fallback_tool"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    SCHEMA_CORRECTION = "schema_correction"


@dataclass
class HealingAction:
    """Record of a self-healing intervention."""
    attempt: int
    category: FailureCategory
    strategy: RecoveryStrategy
    diagnosis: str
    action_taken: str
    success: bool
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class SelfHealingResult:
    """Enriched agent execution result including self-healing telemetry."""
    output: str
    status: Any
    healed: bool = False
    total_attempts: int = 1
    healing_history: List[HealingAction] = field(default_factory=list)
    execution_time: float = 0.0
    tokens_used: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SelfHealingAgentExecutor:
    """
    Supervises agent execution with automated error detection, self-reflection,
    and adaptive recovery.
    """

    def __init__(
        self,
        agent: Agent,
        max_retries: int = 3,
        initial_backoff: float = 0.2,
        backoff_multiplier: float = 2.0,
        circuit_breaker: Optional[CircuitBreaker] = None,
        fallback_tools: Optional[Dict[str, Callable]] = None,
    ):
        self.agent = agent
        self.max_retries = max(1, max_retries)
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            name=f"agent_{getattr(agent, 'id', 'default')}",
            config=CircuitBreakerConfig(failure_threshold=5, timeout=30.0),
        )
        self.fallback_tools = fallback_tools or {}

    def classify_failure(self, error_message: str, error_obj: Optional[Exception] = None) -> FailureCategory:
        """Categorize failure mode from error messages or exceptions."""
        err_lower = (error_message or "").lower()
        if "circuit breaker" in err_lower or "circuit open" in err_lower:
            return FailureCategory.CIRCUIT_OPEN
        if "rate limit" in err_lower or "429" in err_lower or "quota" in err_lower:
            return FailureCategory.RATE_LIMIT
        if "timeout" in err_lower or "timed out" in err_lower or "deadline" in err_lower:
            return FailureCategory.TIMEOUT
        if "tool" in err_lower or "function" in err_lower or "argument" in err_lower:
            return FailureCategory.TOOL_ERROR
        if "json" in err_lower or "schema" in err_lower or "validation" in err_lower or "pydantic" in err_lower:
            return FailureCategory.VALIDATION_ERROR
        if "hallucinat" in err_lower or "invalid format" in err_lower:
            return FailureCategory.HALLUCINATION

        return FailureCategory.UNKNOWN

    def execute(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        expected_schema: Optional[Dict[str, Any]] = None,
    ) -> SelfHealingResult:
        """
        Execute agent with autonomous self-healing and error recovery.
        """
        from agent_factory.agents.agent import AgentResult, AgentStatus

        start_time = time.perf_counter()
        current_prompt = prompt
        current_context = dict(context or {})
        history: List[HealingAction] = []
        tokens_accumulated = 0
        backoff = self.initial_backoff

        for attempt in range(1, self.max_retries + 1):
            try:
                # Check circuit breaker before execution
                with self.circuit_breaker._lock:
                    self.circuit_breaker._update_state()
                    is_circuit_open = self.circuit_breaker.stats.state == CircuitState.OPEN

                if is_circuit_open:
                    action = HealingAction(
                        attempt=attempt,
                        category=FailureCategory.CIRCUIT_OPEN,
                        strategy=RecoveryStrategy.CIRCUIT_BREAKER,
                        diagnosis="Circuit breaker is OPEN due to repeated external failures.",
                        action_taken="Execution halted to protect downstream services.",
                        success=False,
                    )
                    history.append(action)
                    return SelfHealingResult(
                        output="",
                        status=AgentStatus.ERROR,
                        healed=False,
                        total_attempts=attempt,
                        healing_history=history,
                        execution_time=round(time.perf_counter() - start_time, 3),
                        error="Circuit breaker is currently open.",
                    )

                # Execute underlying agent
                result: AgentResult = self.agent.run(current_prompt, context=current_context)
                tokens_accumulated += result.tokens_used

                # Validate execution outcome
                is_error = result.status == AgentStatus.ERROR or bool(result.error)

                # Validate expected JSON schema if requested
                if not is_error and expected_schema:
                    try:
                        parsed = json.loads(result.output)
                        for required_key in expected_schema.get("required", []):
                            if required_key not in parsed:
                                is_error = True
                                result.error = f"Missing required JSON property: {required_key}"
                                break
                    except Exception as parse_err:
                        is_error = True
                        result.error = f"Invalid JSON format for schema: {parse_err}"

                if not is_error:
                    self.circuit_breaker._on_success()
                    was_healed = attempt > 1
                    return SelfHealingResult(
                        output=result.output,
                        status=AgentStatus.COMPLETED,
                        healed=was_healed,
                        total_attempts=attempt,
                        healing_history=history,
                        execution_time=round(time.perf_counter() - start_time, 3),
                        tokens_used=tokens_accumulated,
                        metadata={
                            "agent_id": self.agent.id,
                            "reasoning_content": result.reasoning_content,
                        },
                    )

                # Handle caught error condition
                self.circuit_breaker._on_failure()
                category = self.classify_failure(result.error or "")

                if attempt == self.max_retries:
                    # Final attempt exhausted
                    action = HealingAction(
                        attempt=attempt,
                        category=category,
                        strategy=RecoveryStrategy.RETRY_WITH_REFLECTION,
                        diagnosis=f"Exhausted maximum retry budget ({self.max_retries}).",
                        action_taken="Terminated with error status.",
                        success=False,
                    )
                    history.append(action)
                    break

                # Self-healing synthesis for next iteration
                recovery_strategy, corrective_prompt = self._synthesize_recovery(
                    category=category,
                    original_prompt=prompt,
                    previous_output=result.output,
                    error_message=result.error or "Unknown failure",
                    expected_schema=expected_schema,
                )

                action = HealingAction(
                    attempt=attempt,
                    category=category,
                    strategy=recovery_strategy,
                    diagnosis=f"Detected {category.value}: {result.error}",
                    action_taken=f"Injected reflection prompt ({recovery_strategy.value}).",
                    success=False,
                )
                history.append(action)

                # Apply adaptive delay if rate-limited or transient network error
                if category in (FailureCategory.RATE_LIMIT, FailureCategory.TIMEOUT):
                    time.sleep(backoff)
                    backoff *= self.backoff_multiplier

                current_prompt = corrective_prompt

            except Exception as exc:
                self.circuit_breaker._on_failure()
                category = self.classify_failure(str(exc), exc)

                if attempt == self.max_retries:
                    action = HealingAction(
                        attempt=attempt,
                        category=category,
                        strategy=RecoveryStrategy.RETRY_WITH_REFLECTION,
                        diagnosis=f"Exception raised during attempt: {exc}",
                        action_taken="Terminated with exception.",
                        success=False,
                    )
                    history.append(action)
                    break

                recovery_strategy, corrective_prompt = self._synthesize_recovery(
                    category=category,
                    original_prompt=prompt,
                    previous_output="",
                    error_message=str(exc),
                    expected_schema=expected_schema,
                )
                action = HealingAction(
                    attempt=attempt,
                    category=category,
                    strategy=recovery_strategy,
                    diagnosis=f"Exception encountered: {exc}",
                    action_taken=f"Applying {recovery_strategy.value} and retrying.",
                    success=False,
                )
                history.append(action)
                current_prompt = corrective_prompt

        return SelfHealingResult(
            output="",
            status=AgentStatus.ERROR,
            healed=False,
            total_attempts=self.max_retries,
            healing_history=history,
            execution_time=round(time.perf_counter() - start_time, 3),
            tokens_used=tokens_accumulated,
            error=history[-1].diagnosis if history else "Unknown self-healing failure",
        )

    def _synthesize_recovery(
        self,
        category: FailureCategory,
        original_prompt: str,
        previous_output: str,
        error_message: str,
        expected_schema: Optional[Dict[str, Any]] = None,
    ) -> tuple[RecoveryStrategy, str]:
        """Generate targeted reflection guidance to guide subsequent execution."""
        if category == FailureCategory.VALIDATION_ERROR or expected_schema:
            schema_str = json.dumps(expected_schema) if expected_schema else "{}"
            correction = (
                f"{original_prompt}\n\n"
                f"[SYSTEM SELF-HEALING CORRECTION]: Your previous response failed validation: {error_message}.\n"
                f"You MUST format your output as valid JSON matching this schema exactly:\n{schema_str}\n"
                f"Do NOT include markdown backticks or commentary. Output raw JSON only."
            )
            return RecoveryStrategy.SCHEMA_CORRECTION, correction

        if category == FailureCategory.TOOL_ERROR:
            correction = (
                f"{original_prompt}\n\n"
                f"[SYSTEM SELF-HEALING CORRECTION]: Tool call resulted in an error: {error_message}.\n"
                f"Review the required parameter types and constraints before proceeding.\n"
                f"Previous output snippet: {previous_output[:200]}"
            )
            return RecoveryStrategy.FALLBACK_TOOL, correction

        if category == FailureCategory.RATE_LIMIT:
            correction = (
                f"{original_prompt}\n\n"
                f"[SYSTEM SELF-HEALING NOTE]: Upstream throttling detected. Please formulate a concise, direct answer."
            )
            return RecoveryStrategy.EXPONENTIAL_BACKOFF, correction

        # General reflection fallback
        correction = (
            f"{original_prompt}\n\n"
            f"[SYSTEM SELF-HEALING REFLECTION]: A previous attempt failed with: '{error_message}'.\n"
            f"Carefully evaluate what went wrong and provide a corrected, robust response."
        )
        return RecoveryStrategy.RETRY_WITH_REFLECTION, correction
