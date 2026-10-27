"""Application Performance Monitoring (APM)."""

import os
import time
from functools import wraps
from typing import Any


class APMClient:
    """Simple APM client for performance monitoring."""

    def __init__(self):
        self.enabled = os.getenv("APM_ENABLED", "false").lower() == "true"
        self.metrics: dict[str, list] = {}

    def record_timing(
        self, operation: str, duration: float, tags: dict[str, str] | None = None
    ) -> None:
        """
        Record timing metric.

        Args:
            operation: Operation name
            duration: Duration in seconds
            tags: Optional tags
        """
        if not self.enabled:
            return

        if operation not in self.metrics:
            self.metrics[operation] = []

        self.metrics[operation].append(
            {
                "duration": duration,
                "tags": tags or {},
                "timestamp": time.time(),
            }
        )

    def record_counter(
        self, metric: str, value: float = 1.0, tags: dict[str, str] | None = None
    ) -> None:
        """
        Record counter metric.

        Args:
            metric: Metric name
            value: Counter value
            tags: Optional tags
        """
        if not self.enabled:
            return

        # Could integrate with Prometheus or other metrics backend

    def get_stats(self, operation: str) -> dict[str, Any] | None:
        """
        Get statistics for an operation.

        Args:
            operation: Operation name

        Returns:
            Statistics dict or None
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return None

        durations = [m["duration"] for m in self.metrics[operation]]

        return {
            "count": len(durations),
            "min": min(durations),
            "max": max(durations),
            "avg": sum(durations) / len(durations),
            "p95": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "p99": sorted(durations)[int(len(durations) * 0.99)] if durations else 0,
        }


# Global APM client instance
_apm_client: APMClient | None = None


def get_apm_client() -> APMClient:
    """Get global APM client instance."""
    global _apm_client
    if _apm_client is None:
        _apm_client = APMClient()
    return _apm_client


def trace_operation(operation_name: str):
    """
    Decorator to trace operation performance.

    Args:
        operation_name: Name of the operation
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            apm = get_apm_client()
            if not apm.enabled:
                return await func(*args, **kwargs)

            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                apm.record_timing(operation_name, duration, {"status": "success"})
                return result
            except Exception as e:
                duration = time.time() - start
                apm.record_timing(
                    operation_name, duration, {"status": "error", "error_type": type(e).__name__}
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            apm = get_apm_client()
            if not apm.enabled:
                return func(*args, **kwargs)

            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                apm.record_timing(operation_name, duration, {"status": "success"})
                return result
            except Exception as e:
                duration = time.time() - start
                apm.record_timing(
                    operation_name, duration, {"status": "error", "error_type": type(e).__name__}
                )
                raise

        if hasattr(func, "__code__") and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def setup_apm(app) -> None:
    """
    Setup APM for FastAPI app.

    Args:
        app: FastAPI application
    """
    apm = get_apm_client()
    if not apm.enabled:
        return

    # Add APM stats endpoint
    @app.get("/api/v1/apm/stats")
    async def apm_stats():
        """Get APM statistics."""
        stats = {}
        for operation in apm.metrics:
            stats[operation] = apm.get_stats(operation)
        return stats
