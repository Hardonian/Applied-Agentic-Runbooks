"""Tests for billing system."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from agent_factory.billing.model import Plan, Subscription, UsageRecord
from agent_factory.billing.plans import get_plan, list_plans
from agent_factory.billing.usage_tracker import UsageTracker, get_usage_tracker


@pytest.mark.unit
def test_plan_model():
    """Test Plan model."""
    plan = Plan(
        id="free",
        name="Free Plan",
        price=0.0,
        currency="USD",
        features={"max_agents": 5},
    )

    assert plan.id == "free"
    assert plan.price == 0.0
    assert plan.features["max_agents"] == 5


@pytest.mark.unit
def test_subscription_model():
    """Test Subscription model."""
    subscription = Subscription(
        id="sub-123",
        tenant_id="tenant-1",
        plan_id="pro",
        status="active",
        current_period_start=datetime.utcnow(),
    )

    assert subscription.id == "sub-123"
    assert subscription.status == "active"


@pytest.mark.unit
def test_usage_record_model():
    """Test UsageRecord model."""
    record = UsageRecord(
        id="usage-123",
        tenant_id="tenant-1",
        billing_unit="agent_run",
        quantity=10.0,
        period_start=datetime.utcnow(),
    )

    assert record.tenant_id == "tenant-1"
    assert record.quantity == 10.0


@pytest.mark.unit
@patch("agent_factory.billing.usage_tracker.get_collector")
def test_usage_tracker_record_agent_run(mock_get_collector):
    """Test recording an agent run."""
    mock_collector = Mock()
    mock_get_collector.return_value = mock_collector

    tracker = UsageTracker()
    tracker.record_agent_run(
        tenant_id="tenant-1",
        tokens_used=100,
        cost_estimate=0.01,
    )

    # Should record billing usage
    assert mock_collector.record_billing_usage.called
    call_args = mock_collector.record_billing_usage.call_args
    assert call_args[1]["billing_unit"] == "agent_run"
    assert call_args[1]["quantity"] == 1.0


@pytest.mark.unit
@patch("agent_factory.billing.usage_tracker.get_collector")
def test_usage_tracker_record_workflow_run(mock_get_collector):
    """Test recording a workflow run."""
    mock_collector = Mock()
    mock_get_collector.return_value = mock_collector

    tracker = UsageTracker()
    tracker.record_workflow_run(
        tenant_id="tenant-1",
        tokens_used=200,
    )

    assert mock_collector.record_billing_usage.called


@pytest.mark.unit
def test_get_usage_tracker_singleton():
    """Test get_usage_tracker returns singleton."""
    tracker1 = get_usage_tracker()
    tracker2 = get_usage_tracker()

    assert tracker1 is tracker2


@pytest.mark.unit
@patch("agent_factory.billing.plans.get_db")
def test_get_plan(mock_get_db):
    """Test getting a plan."""
    mock_db = Mock()
    mock_plan = Mock()
    mock_plan.id = "free"
    mock_plan.name = "Free Plan"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_plan
    mock_get_db.return_value = iter([mock_db])

    plan = get_plan("free")

    assert plan is not None


@pytest.mark.unit
@patch("agent_factory.billing.plans.get_db")
def test_list_plans(mock_get_db):
    """Test listing plans."""
    mock_db = Mock()
    mock_plan = Mock()
    mock_plan.id = "free"
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_plan]
    mock_get_db.return_value = iter([mock_db])

    plans = list_plans()

    assert len(plans) == 1
