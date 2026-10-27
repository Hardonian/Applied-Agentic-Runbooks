"""Sentry error tracking integration."""

import os


def setup_sentry() -> object | None:
    """
    Setup Sentry error tracking.

    Returns:
        Sentry client if configured, None otherwise
    """
    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        return None

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.getenv("ENVIRONMENT", "development"),
            release=os.getenv("SENTRY_RELEASE"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            before_send=before_send_handler,
        )

        return sentry_sdk
    except ImportError:
        # Sentry SDK not installed
        return None
    except Exception as e:
        # Sentry setup failed, but don't break the app
        print(f"Warning: Sentry setup failed: {e}")
        return None


def before_send_handler(event: dict, hint: dict) -> dict | None:
    """
    Filter events before sending to Sentry.

    Args:
        event: Sentry event
        hint: Event hint

    Returns:
        Event dict if should send, None otherwise
    """
    # Filter out health check errors
    if event.get("request", {}).get("url", "").endswith("/health"):
        return None

    # Filter out liveness/readiness probe errors
    if event.get("request", {}).get("url", "").endswith(("/live", "/ready")):
        return None

    return event


def capture_exception(error: Exception, **kwargs) -> None:
    """
    Capture exception in Sentry.

    Args:
        error: Exception to capture
        **kwargs: Additional context
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in kwargs.items():
                scope.set_context(key, value)
            sentry_sdk.capture_exception(error)
    except (
        Exception
    ):  # nosec B110 -- error reporting must never raise: Sentry may be unconfigured or down, and failing here would mask the original error
        # Sentry not available or failed, ignore
        pass


def capture_message(message: str, level: str = "info", **kwargs) -> None:
    """
    Capture message in Sentry.

    Args:
        message: Message to capture
        level: Log level (info, warning, error)
        **kwargs: Additional context
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in kwargs.items():
                scope.set_context(key, value)
            sentry_sdk.capture_message(message, level=level)
    except (
        Exception
    ):  # nosec B110 -- message reporting must never raise: Sentry may be unconfigured or down
        # Sentry not available or failed, ignore
        pass
