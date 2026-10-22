"""Distributed tracing support."""

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed tracing."""

    async def dispatch(self, request: Request, call_next):
        """Add tracing headers to request."""
        # Get or create trace ID
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        span_id = request.headers.get("X-Span-Id") or str(uuid.uuid4())

        # Add to request state
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        # Process request
        response = await call_next(request)

        # Add tracing headers to response
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Span-Id"] = span_id

        return response


def setup_tracing(app):
    """Setup distributed tracing for FastAPI app."""
    app.add_middleware(TracingMiddleware)
    return app
