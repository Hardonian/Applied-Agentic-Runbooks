"""Tests for payments functionality."""


import pytest

from agent_factory.payments.revenue_sharing import calculate_revenue_share


@pytest.mark.unit
def test_calculate_revenue_share():
    """Test calculating revenue share."""
    result = calculate_revenue_share(100.0)
    
    assert result["total"] == 100.0
    assert result["platform_fee"] == 30.0
    assert result["creator_fee"] == 70.0
    assert result["platform_fee_percentage"] == 0.30
    assert result["creator_fee_percentage"] == 0.70


@pytest.mark.unit
def test_calculate_revenue_share_zero():
    """Test calculating revenue share for zero amount."""
    result = calculate_revenue_share(0.0)
    
    assert result["total"] == 0.0
    assert result["platform_fee"] == 0.0
    assert result["creator_fee"] == 0.0
