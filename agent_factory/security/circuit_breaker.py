"""
Circuit breaker pattern for resilient external service calls.

Implements circuit breaker to prevent cascading failures when external services
are unavailable or experiencing issues.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Any


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Open circuit after N failures
    success_threshold: int = 2  # Close circuit after N successes
    timeout: float = 60.0  # Seconds before attempting half-open
    expected_exception: type = Exception  # Exception type to catch


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    failures: int = 0
    successes: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: float | None = None
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0


class CircuitBreaker:
    """
    Circuit breaker for resilient service calls.
    
    Example:
        >>> breaker = CircuitBreaker("openai_api")
        >>> result = breaker.call(openai_client.chat.completions.create, ...)
    """
    
    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            config: Optional configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if call fails
        """
        with self._lock:
            self._update_state()
            
            if self.stats.state == CircuitState.OPEN:
                from agent_factory.core.exceptions import AgentFactoryError
                raise AgentFactoryError(
                    f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
                )
        
        # Attempt call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception:
            self._on_failure()
            raise
    
    def _update_state(self) -> None:
        """Update circuit breaker state based on current conditions."""
        current_time = time.time()
        
        if self.stats.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.stats.last_failure_time:
                elapsed = current_time - self.stats.last_failure_time
                if elapsed >= self.config.timeout:
                    self.stats.state = CircuitState.HALF_OPEN
                    self.stats.failures = 0
                    self.stats.successes = 0
        
        elif self.stats.state == CircuitState.HALF_OPEN:
            # Already handled in _on_success/_on_failure
            pass
        
        elif self.stats.state == CircuitState.CLOSED:
            # Check if we should open
            if self.stats.failures >= self.config.failure_threshold:
                self.stats.state = CircuitState.OPEN
                self.stats.last_failure_time = current_time
    
    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            self.stats.total_calls += 1
            self.stats.total_successes += 1
            
            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.successes += 1
                if self.stats.successes >= self.config.success_threshold:
                    self.stats.state = CircuitState.CLOSED
                    self.stats.failures = 0
                    self.stats.successes = 0
            elif self.stats.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.stats.failures = 0
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        with self._lock:
            self.stats.total_calls += 1
            self.stats.total_failures += 1
            self.stats.failures += 1
            self.stats.last_failure_time = time.time()
            
            if self.stats.state == CircuitState.HALF_OPEN:
                # Failed in half-open, go back to open
                self.stats.state = CircuitState.OPEN
                self.stats.successes = 0
            elif self.stats.state == CircuitState.CLOSED:
                # Check if we should open
                if self.stats.failures >= self.config.failure_threshold:
                    self.stats.state = CircuitState.OPEN
    
    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.stats.state.value,
                "failures": self.stats.failures,
                "successes": self.stats.successes,
                "total_calls": self.stats.total_calls,
                "total_failures": self.stats.total_failures,
                "total_successes": self.stats.total_successes,
                "last_failure_time": self.stats.last_failure_time,
            }
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        with self._lock:
            self.stats.state = CircuitState.CLOSED
            self.stats.failures = 0
            self.stats.successes = 0
            self.stats.last_failure_time = None


# Global circuit breakers
_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    """
    Get or create a circuit breaker.
    
    Args:
        name: Circuit breaker name
        config: Optional configuration
        
    Returns:
        Circuit breaker instance
    """
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name, config)
    return _breakers[name]
