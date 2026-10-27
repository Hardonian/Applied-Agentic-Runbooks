"""Tests for analytics engine."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from agent_factory.telemetry.analytics import AnalyticsEngine, get_analytics
from agent_factory.telemetry.collector import TelemetryCollector
from agent_factory.telemetry.model import (
    AgentRunEvent,
    BlueprintInstallEvent,
    ErrorEvent,
    EventType,
)


@pytest.mark.unit
def test_analytics_engine_initialization():
    """Test analytics engine initialization."""
    collector = Mock(spec=TelemetryCollector)
    analytics = AnalyticsEngine(collector=collector)

    assert analytics.collector == collector


@pytest.mark.unit
def test_get_growth_summary():
    """Test getting growth summary."""
    collector = Mock(spec=TelemetryCollector)

    # Mock events
    events = [
        AgentRunEvent(
            event_id="1",
            event_type=EventType.AGENT_RUN,
            agent_id="agent-1",
            tenant_id="tenant-1",
            user_id="user-1",
            tokens_used=100,
            cost_estimate=0.01,
        ),
        AgentRunEvent(
            event_id="2",
            event_type=EventType.AGENT_RUN,
            agent_id="agent-2",
            tenant_id="tenant-1",
            user_id="user-2",
            tokens_used=200,
            cost_estimate=0.02,
        ),
    ]

    collector.query_events.return_value = events

    analytics = AnalyticsEngine(collector=collector)
    summary = analytics.get_growth_summary()

    assert "dau" in summary
    assert "wau" in summary
    assert "mau" in summary
    assert summary["total_agent_runs"] == 2
    assert summary["total_tokens_used"] == 300
    assert summary["total_cost_estimate"] == 0.03


@pytest.mark.unit
def test_get_tenant_metrics():
    """Test getting tenant-specific metrics."""
    collector = Mock(spec=TelemetryCollector)

    events = [
        AgentRunEvent(
            event_id="1",
            event_type=EventType.AGENT_RUN,
            agent_id="agent-1",
            tenant_id="tenant-1",
            tokens_used=100,
        ),
    ]

    collector.query_events.return_value = events

    analytics = AnalyticsEngine(collector=collector)
    metrics = analytics.get_tenant_metrics("tenant-1")

    assert metrics["tenant_id"] == "tenant-1"
    assert metrics["total_agent_runs"] == 1
    assert "error_rate" in metrics


@pytest.mark.unit
def test_get_conversion_funnel():
    """Test getting conversion funnel metrics."""
    collector = Mock(spec=TelemetryCollector)

    events = [
        BlueprintInstallEvent(
            event_id="1",
            event_type=EventType.BLUEPRINT_INSTALL,
            blueprint_id="blueprint-1",
            install_type="install",
        ),
    ]

    collector.query_events.return_value = events

    analytics = AnalyticsEngine(collector=collector)
    funnel = analytics.get_conversion_funnel()

    assert "notebooks_converted" in funnel
    assert "agents_created" in funnel
    assert "blueprints_installed" in funnel
    assert "conversion_rates" in funnel


@pytest.mark.unit
def test_compute_dau():
    """Test computing Daily Active Users."""
    collector = Mock(spec=TelemetryCollector)

    now = datetime.utcnow()
    events = [
        AgentRunEvent(
            event_id="1",
            event_type=EventType.AGENT_RUN,
            agent_id="agent-1",
            user_id="user-1",
            timestamp=now,
        ),
        AgentRunEvent(
            event_id="2",
            event_type=EventType.AGENT_RUN,
            agent_id="agent-2",
            user_id="user-2",
            timestamp=now,
        ),
    ]

    collector.query_events.return_value = events

    analytics = AnalyticsEngine(collector=collector)
    summary = analytics.get_growth_summary(end_date=now)

    assert summary["dau"] == 2


@pytest.mark.unit
def test_count_unique_agents():
    """Test counting unique agents."""
    collector = Mock(spec=TelemetryCollector)

    events = [
        AgentRunEvent(
            event_id="1",
            event_type=EventType.AGENT_RUN,
            agent_id="agent-1",
        ),
        AgentRunEvent(
            event_id="2",
            event_type=EventType.AGENT_RUN,
            agent_id="agent-2",
        ),
        AgentRunEvent(
            event_id="3",
            event_type=EventType.AGENT_RUN,
            agent_id="agent-1",  # Duplicate
        ),
    ]

    collector.query_events.return_value = events

    analytics = AnalyticsEngine(collector=collector)
    summary = analytics.get_growth_summary()

    assert summary["active_agents"] == 2


@pytest.mark.unit
def test_compute_error_rate():
    """Test computing error rate."""
    collector = Mock(spec=TelemetryCollector)

    events = [
        AgentRunEvent(
            event_id="1",
            event_type=EventType.AGENT_RUN,
            agent_id="agent-1",
        ),
        ErrorEvent(
            event_id="2",
            event_type=EventType.ERROR,
            error_type="ValueError",
            error_message="Test",
        ),
    ]

    collector.query_events.return_value = events

    analytics = AnalyticsEngine(collector=collector)
    metrics = analytics.get_tenant_metrics("tenant-1")

    assert metrics["error_rate"] == 0.5  # 1 error / 2 total events


@pytest.mark.unit
def test_get_analytics_singleton():
    """Test get_analytics returns singleton."""
    analytics1 = get_analytics()
    analytics2 = get_analytics()

    assert analytics1 is analytics2
