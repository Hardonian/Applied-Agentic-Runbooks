"""Tests for enterprise compliance features."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from agent_factory.enterprise.compliance import export_user_data, delete_user_data, enforce_data_retention


@pytest.mark.unit
def test_export_user_data():
    """Test exporting user data for GDPR."""
    with patch('agent_factory.enterprise.compliance.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_user = Mock()
        mock_user.id = "user1"
        mock_user.email = "user@example.com"
        mock_user.created_at = datetime.now()
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = export_user_data("user1")
        
        assert "user" in result
        assert result["user"]["id"] == "user1"
        assert "exported_at" in result


@pytest.mark.unit
def test_enforce_data_retention():
    """Test enforcing data retention policy."""
    with patch('agent_factory.enterprise.compliance.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 5
        
        mock_db.query.return_value = mock_query
        
        result = enforce_data_retention("tenant1", retention_days=90)
        
        assert "deleted_logs" in result
        assert "deleted_executions" in result
