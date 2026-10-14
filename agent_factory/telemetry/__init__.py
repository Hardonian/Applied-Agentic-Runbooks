"""
Telemetry and analytics system for Agent Factory Platform.

Provides comprehensive tracking of:
- Agent runs
- Workflow runs
- Blueprint installations
- Error events
- Billing usage events
- Growth metrics
"""

from agent_factory.telemetry.analytics import AnalyticsEngine, get_analytics
from agent_factory.telemetry.backends.base import TelemetryBackend
from agent_factory.telemetry.backends.sqlite import SQLiteTelemetryBackend
from agent_factory.telemetry.collector import TelemetryCollector, get_collector
from agent_factory.telemetry.model import (
    AgentRunEvent,
    BillingUsageEvent,
    BlueprintInstallEvent,
    ErrorEvent,
    ProjectEvent,
    ReferralEvent,
    RevenueEvent,
    TelemetryEvent,
    TenantEvent,
    UserActivatedEvent,
    UserLoginEvent,
    UserSignupEvent,
    WorkflowRunEvent,
)
from agent_factory.telemetry.pcap import (
    AgentPCAPTracer,
    FrameType,
    PathologyDiagnostic,
    PathologyType,
    PCAPFrame,
)

try:
    from agent_factory.telemetry.revenue import RevenueTracker, get_revenue_tracker
except ImportError:
    RevenueTracker = None
    get_revenue_tracker = None

# Lazy import for PostgresTelemetryBackend
def __getattr__(name: str):
    """Lazy import for PostgresTelemetryBackend."""
    if name == "PostgresTelemetryBackend":
        from agent_factory.telemetry.backends import PostgresTelemetryBackend
        return PostgresTelemetryBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "AgentPCAPTracer",
    "AgentRunEvent",
    "AnalyticsEngine",
    "BillingUsageEvent",
    "BlueprintInstallEvent",
    "ErrorEvent",
    "FrameType",
    "PCAPFrame",
    "PathologyDiagnostic",
    "PathologyType",
    "PostgresTelemetryBackend",
    "ProjectEvent",
    "ReferralEvent",
    "RevenueEvent",
    "RevenueTracker",
    "SQLiteTelemetryBackend",
    "TelemetryBackend",
    "TelemetryCollector",
    "TelemetryEvent",
    "TenantEvent",
    "UserActivatedEvent",
    "UserLoginEvent",
    "UserSignupEvent",
    "WorkflowRunEvent",
    "get_analytics",
    "get_collector",
    "get_revenue_tracker",
]
from agent_factory.telemetry.otel_exporter import OpenTelemetryBridge, OTelExporter

__all__ = ["OpenTelemetryBridge", "OTelExporter"]
