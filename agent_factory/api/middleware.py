"""
Enhanced API middleware for security and observability.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from agent_factory.monitoring import setup_structured_logging
import os

logger = setup_structured_logging(os.getenv("LOG_LEVEL", "INFO"))


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID for tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request and response."""
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to add timing information."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add timing headers to response."""
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        return response
