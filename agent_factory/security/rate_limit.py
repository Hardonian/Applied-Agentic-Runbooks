"""Rate limiting middleware."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI app
            requests_per_minute: Max requests per minute per IP
            requests_per_hour: Max requests per hour per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests: dict[str, list] = defaultdict(list)
        self.hour_requests: dict[str, list] = defaultdict(list)

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        if request.client:
            return request.client.host
        return "unknown"

    def cleanup_old_requests(self, requests_list: list, window_seconds: int):
        """Remove requests outside time window."""
        current_time = time.time()
        cutoff = current_time - window_seconds
        return [req_time for req_time in requests_list if req_time > cutoff]

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        import os

        if (
            os.getenv("TESTING", "").lower() in ("true", "1", "yes")
            or os.getenv("RATE_LIMIT_DISABLED", "").lower() in ("true", "1", "yes")
            or os.getenv("ENVIRONMENT") == "test"
        ):
            return await call_next(request)

        client_ip = self.get_client_ip(request)
        current_time = time.time()

        # Clean up old requests
        self.minute_requests[client_ip] = self.cleanup_old_requests(
            self.minute_requests[client_ip], 60
        )
        self.hour_requests[client_ip] = self.cleanup_old_requests(
            self.hour_requests[client_ip], 3600
        )

        # Check rate limits
        minute_count = len(self.minute_requests[client_ip])
        hour_count = len(self.hour_requests[client_ip])

        if minute_count >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many requests per minute",
            )

        if hour_count >= self.requests_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many requests per hour",
            )

        # Record request
        self.minute_requests[client_ip].append(current_time)
        self.hour_requests[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            self.requests_per_minute - minute_count - 1
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            self.requests_per_hour - hour_count - 1
        )

        return response


def setup_rate_limiting(app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
    """
    Setup rate limiting for FastAPI app.

    Args:
        app: FastAPI app
        requests_per_minute: Max requests per minute
        requests_per_hour: Max requests per hour
    """
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
    )
    return app
