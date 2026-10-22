"""
FastAPI REST API main application.
"""

# ruff: noqa: E402 — routers are imported after app creation by design

import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent_factory.api.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    TimingMiddleware,
)
from agent_factory.api.routes import agents, blueprints, executions, telemetry, tools, workflows
from agent_factory.cache import get_cache
from agent_factory.database import init_db
from agent_factory.monitoring import setup_metrics, setup_structured_logging, setup_tracing
from agent_factory.monitoring.apm import setup_apm
from agent_factory.monitoring.sentry import setup_sentry
from agent_factory.security import setup_rate_limiting

# Setup structured logging first
logger = setup_structured_logging(os.getenv("LOG_LEVEL", "INFO"))

# Setup Sentry error tracking (if configured)
sentry_client = setup_sentry()
if sentry_client:
    logger.info("Sentry error tracking enabled")

app = FastAPI(
    title="Agent Factory Platform API",
    description="REST API for building and running AI agents",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup monitoring
setup_metrics(app)
setup_tracing(app)
setup_apm(app)

# Setup rate limiting
setup_rate_limiting(
    app,
    requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
    requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add request ID middleware for tracing
app.add_middleware(RequestIDMiddleware)

# Add timing middleware
app.add_middleware(TimingMiddleware)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    try:
        # Validate environment variables
        from agent_factory.utils.env_validator import validate_agent_factory_env

        validated_env = validate_agent_factory_env()
        logger.info("Environment variables validated", validated_count=len(validated_env))

        # Initialize database
        init_db()
        logger.info("Database initialized")

        # Initialize cache
        cache = get_cache()
        if cache:
            logger.info("Cache initialized")

    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise


# Include routers
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(blueprints.router, prefix="/api/v1/blueprints", tags=["blueprints"])
app.include_router(executions.router, prefix="/api/v1/executions", tags=["executions"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["telemetry"])

# Authentication routes
from agent_factory.api.routes import auth

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# Additional routers
from agent_factory.api.routes import (
    financial,
    metrics_dashboard,
    payments,
    referrals,
    research,
    scheduler,
)
from agent_factory.api.routes import health as health_routes

app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["scheduler"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(health_routes.router, prefix="/api/v1/health", tags=["health"])
app.include_router(financial.router, prefix="/api/v1/financial", tags=["financial"])
app.include_router(
    research.router, prefix="/api/v1", tags=["research"]
)  # Product surface at root level
app.include_router(referrals.router, tags=["referrals"])
app.include_router(metrics_dashboard.router, tags=["metrics"])


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests."""
    logger.info(
        "Request received",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
    )

    response = await call_next(request)

    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler with enhanced error reporting.

    Provides detailed error information in development mode,
    generic messages in production for security.
    """
    import traceback

    from agent_factory.core.exceptions import AgentFactoryError
    from agent_factory.monitoring.sentry import capture_exception

    # Determine if we're in debug mode
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    # Capture exception in Sentry
    capture_exception(
        exc,
        request_path=request.url.path,
        request_method=request.method,
        query_params=dict(request.query_params) if request.query_params else None,
    )

    # Log the exception
    logger.exception(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        query_params=dict(request.query_params) if request.query_params else None,
    )

    # Handle known exceptions
    if isinstance(exc, AgentFactoryError):
        # Use specific error handling for known exceptions
        error_detail = {
            "error": type(exc).__name__,
            "message": str(exc),
        }

        # Add stack trace in debug mode
        if debug_mode:
            error_detail["traceback"] = traceback.format_exc()

        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=error_detail)

    # Handle validation errors (Pydantic)
    if hasattr(exc, "errors"):
        error_detail = {
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors() if callable(exc.errors) else exc.errors,
        }
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_detail)

    # Generic error response
    error_detail = {
        "error": "InternalServerError",
        "message": "An internal server error occurred",
    }

    # Add detailed information in debug mode
    if debug_mode:
        error_detail["exception_type"] = type(exc).__name__
        error_detail["exception_message"] = str(exc)
        error_detail["traceback"] = traceback.format_exc()

    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_detail)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Agent Factory Platform API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """
    Comprehensive health check endpoint.

    Returns status of all critical dependencies:
    - Database connectivity
    - Cache/Redis connectivity
    - LLM provider availability (if configured)

    Status codes:
    - 200: All systems healthy
    - 503: One or more systems degraded
    """
    import time
    from datetime import datetime

    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "checks": {},
    }

    overall_healthy = True

    # Check database
    db_check = {"status": "unknown", "response_time_ms": 0}
    try:
        from agent_factory.database.session import engine

        db_start = time.time()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_check["status"] = "healthy"
        db_check["response_time_ms"] = round((time.time() - db_start) * 1000, 2)
    except Exception as e:
        db_check["status"] = "unhealthy"
        db_check["error"] = str(e)
        overall_healthy = False
        logger.error("Database health check failed", error=str(e))
    health_status["checks"]["database"] = db_check

    # Check cache
    cache_check = {"status": "unknown", "response_time_ms": 0}
    try:
        cache = get_cache()
        if cache.client:
            cache_start = time.time()
            cache.client.ping()
            cache_check["status"] = "healthy"
            cache_check["response_time_ms"] = round((time.time() - cache_start) * 1000, 2)
        else:
            cache_check["status"] = "unavailable"
            cache_check["message"] = "Cache client not initialized"
    except Exception as e:
        cache_check["status"] = "unhealthy"
        cache_check["error"] = str(e)
        overall_healthy = False
        logger.error("Cache health check failed", error=str(e))
    health_status["checks"]["cache"] = cache_check

    # Check LLM providers (optional, don't fail if not configured)
    llm_check = {"status": "unknown"}
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if openai_key or anthropic_key:
            llm_check["status"] = "configured"
            llm_check["providers"] = []
            if openai_key:
                llm_check["providers"].append("openai")
            if anthropic_key:
                llm_check["providers"].append("anthropic")
        else:
            llm_check["status"] = "not_configured"
            llm_check["message"] = "No LLM providers configured (optional)"
    except Exception as e:
        llm_check["status"] = "error"
        llm_check["error"] = str(e)
    health_status["checks"]["llm_providers"] = llm_check

    # Set overall status
    if not overall_healthy:
        health_status["status"] = "degraded"

    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/ready")
async def readiness():
    """Readiness probe endpoint."""
    try:
        from agent_factory.database.session import engine

        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        return JSONResponse(
            content={"status": "not ready"}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@app.get("/live")
async def liveness():
    """Liveness probe endpoint."""
    return {"status": "alive"}
