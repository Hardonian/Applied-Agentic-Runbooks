"""Prometheus metrics collection."""

import time

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

# Metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"]
)

agent_executions_total = Counter(
    "agent_executions_total", "Total agent executions", ["agent_id", "status"]
)

agent_execution_duration_seconds = Histogram(
    "agent_execution_duration_seconds", "Agent execution duration in seconds", ["agent_id"]
)

workflow_executions_total = Counter(
    "workflow_executions_total", "Total workflow executions", ["workflow_id", "status"]
)

workflow_execution_duration_seconds = Histogram(
    "workflow_execution_duration_seconds", "Workflow execution duration in seconds", ["workflow_id"]
)

active_sessions = Gauge("active_sessions", "Number of active agent sessions")

active_executions = Gauge("active_executions", "Number of active executions")

cache_hits_total = Counter("cache_hits_total", "Total cache hits", ["cache_type"])

cache_misses_total = Counter("cache_misses_total", "Total cache misses", ["cache_type"])

arena_runs_total = Counter(
    "agent_factory_arena_runs_total",
    "Durable Arena runs by terminal status and mode",
    ["status", "mode"],
)
arena_run_duration_seconds = Histogram(
    "agent_factory_arena_run_duration_seconds",
    "Arena run wall-clock duration",
    ["mode"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 5, 15, 60, 300, 900),
)
arena_cost_usd = Histogram(
    "agent_factory_arena_cost_usd",
    "Arena estimated run cost in USD",
    buckets=(0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000),
)
arena_pass_rate = Gauge(
    "agent_factory_arena_last_pass_rate",
    "Pass rate of the most recently completed Arena run",
    ["mode"],
)
websocket_subscribers = Gauge(
    "agent_factory_websocket_subscribers",
    "Current WebSocket event subscriptions",
)
websocket_dropped_events_total = Counter(
    "agent_factory_websocket_dropped_events_total",
    "Events dropped for lagging WebSocket consumers",
)
mcpwall_approval_total = Counter(
    "agent_factory_mcpwall_approval_total",
    "MCPWall operator decisions",
    ["decision"],
)


class MetricsCollector:
    """Metrics collector for Agent Factory Platform."""

    @staticmethod
    def record_agent_execution(agent_id: str, duration: float, status: str):
        """Record agent execution metrics."""
        agent_executions_total.labels(agent_id=agent_id, status=status).inc()
        agent_execution_duration_seconds.labels(agent_id=agent_id).observe(duration)

    @staticmethod
    def record_workflow_execution(workflow_id: str, duration: float, status: str):
        """Record workflow execution metrics."""
        workflow_executions_total.labels(workflow_id=workflow_id, status=status).inc()
        workflow_execution_duration_seconds.labels(workflow_id=workflow_id).observe(duration)

    @staticmethod
    def record_cache_hit(cache_type: str):
        """Record cache hit."""
        cache_hits_total.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_cache_miss(cache_type: str):
        """Record cache miss."""
        cache_misses_total.labels(cache_type=cache_type).inc()

    @staticmethod
    def set_active_sessions(count: int):
        """Set active sessions count."""
        active_sessions.set(count)

    @staticmethod
    def set_active_executions(count: int):
        """Set active executions count."""
        active_executions.set(count)

    @staticmethod
    def record_arena_run(status: str, mode: str, duration: float, cost: float, pass_rate: float):
        arena_runs_total.labels(status=status, mode=mode).inc()
        arena_run_duration_seconds.labels(mode=mode).observe(duration)
        arena_cost_usd.observe(cost)
        arena_pass_rate.labels(mode=mode).set(pass_rate)

    @staticmethod
    def set_websocket_subscribers(count: int):
        websocket_subscribers.set(count)

    @staticmethod
    def record_websocket_drop():
        websocket_dropped_events_total.inc()

    @staticmethod
    def record_approval(decision: str):
        mcpwall_approval_total.labels(decision=decision).inc()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""

    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        start_time = time.time()

        # Get endpoint path (remove query params)
        endpoint = request.url.path

        # Call next middleware/route
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=request.method, endpoint=endpoint, status_code=response.status_code
        ).inc()

        http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(
            duration
        )

        return response


def setup_metrics(app):
    """Setup Prometheus metrics for FastAPI app."""
    app.add_middleware(MetricsMiddleware)

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
