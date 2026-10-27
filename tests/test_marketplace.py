"""Tests for marketplace functionality."""

from unittest.mock import Mock, patch

import pytest

from agent_factory.marketplace import get_blueprint_details, search_blueprints


@pytest.mark.unit
def test_search_blueprints():
    """Test searching blueprints."""
    with (
        patch("agent_factory.marketplace.search.get_db") as mock_get_db,
        patch("agent_factory.marketplace.search.get_cache") as mock_cache,
    ):
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value.all.return_value = []

        mock_db.query.return_value = mock_query

        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = None
        mock_cache.return_value = mock_cache_instance

        results = search_blueprints(query="test")
        assert "total" in results
        assert "blueprints" in results


@pytest.mark.unit
def test_get_blueprint_details_not_found():
    """Test getting non-existent blueprint details."""
    with (
        patch("agent_factory.marketplace.search.get_db") as mock_get_db,
        patch("agent_factory.marketplace.search.get_cache") as mock_cache,
    ):
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        mock_db.query.return_value = mock_query

        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = None
        mock_cache.return_value = mock_cache_instance

        result = get_blueprint_details("nonexistent")
        assert result is None
