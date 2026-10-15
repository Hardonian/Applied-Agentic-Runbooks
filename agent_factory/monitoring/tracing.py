"""W3C trace-context propagation with an optional official OpenTelemetry SDK."""

from __future__ import annotations

import contextvars
import os
import re
import secrets
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
current_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id", default=None
)
current_span_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "span_id", default=None
)


def get_trace_context() -> dict[str, str]:
    """Return the active trace identifiers for events and tool/model calls."""
    trace_id = current_trace_id.get()
    span_id = current_span_id.get()
    return {
        key: value for key, value in {"trace_id": trace_id, "span_id": span_id}.items() if value
    }


class TracingMiddleware(BaseHTTPMiddleware):
    """Accept and emit W3C traceparent while retaining legacy trace headers."""

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        incoming = request.headers.get("traceparent", "")
        match = TRACEPARENT.match(incoming)
        trace_id = match.group(1) if match else secrets.token_hex(16)
        parent_span_id = match.group(2) if match else None
        span_id = secrets.token_hex(8)
        trace_token = current_trace_id.set(trace_id)
        span_token = current_span_id.set(span_id)
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        request.state.parent_span_id = parent_span_id
        try:
            response = await call_next(request)
            response.headers["traceparent"] = f"00-{trace_id}-{span_id}-01"
            response.headers["X-Trace-Id"] = trace_id
            response.headers["X-Span-Id"] = span_id
            return response
        finally:
            current_trace_id.reset(trace_token)
            current_span_id.reset(span_token)


def configure_optional_otel_sdk(service_name: str = "agent-factory") -> bool:
    """Configure the official OTLP SDK when installed; otherwise remain dependency-free."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces"))
        )
        trace.set_tracer_provider(provider)
        return True
    except ImportError:
        return False


def setup_tracing(app: Any) -> Any:
    configure_optional_otel_sdk()
    app.add_middleware(TracingMiddleware)
    return app
