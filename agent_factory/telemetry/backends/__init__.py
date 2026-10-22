"""Telemetry storage backends."""

from agent_factory.telemetry.backends.base import TelemetryBackend
from agent_factory.telemetry.backends.sqlite import SQLiteTelemetryBackend


# Lazy import Postgres backend to avoid requiring sqlalchemy at import time
def __getattr__(name: str):
    """Lazy import for PostgresTelemetryBackend."""
    if name == "PostgresTelemetryBackend":
        try:
            from agent_factory.telemetry.backends.postgres import PostgresTelemetryBackend

            return PostgresTelemetryBackend
        except ImportError:
            raise ImportError(
                "PostgresTelemetryBackend requires sqlalchemy. "
                "Install with: pip install sqlalchemy psycopg2-binary"
            ) from None
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "TelemetryBackend",
    "SQLiteTelemetryBackend",
    "PostgresTelemetryBackend",
]
