"""Tests for audit logging."""

from unittest.mock import Mock, patch

import pytest

from agent_factory.security.audit import AuditLogger, audit_log


@pytest.mark.unit
@patch('agent_factory.security.audit.StructuredLogger')
def test_audit_logger_initialization(mock_logger_class):
    """Test audit logger initialization."""
    logger = AuditLogger()
    
    assert logger.logger is not None
    mock_logger_class.assert_called_once_with("audit", level="INFO")


@pytest.mark.unit
@patch('agent_factory.security.audit.StructuredLogger')
def test_audit_logger_log_event(mock_logger_class):
    """Test logging an audit event."""
    mock_logger = Mock()
    mock_logger_class.return_value = mock_logger
    
    logger = AuditLogger()
    logger.log_event(
        event_type="user_login",
        user_id="user-123",
        action="login",
        success=True,
    )
    
    assert mock_logger.info.called
    call_args = mock_logger.info.call_args
    assert "user_login" in call_args[0][0]
    assert call_args[1]["user_id"] == "user-123"


@pytest.mark.unit
@patch('agent_factory.security.audit.StructuredLogger')
def test_audit_logger_log_event_with_details(mock_logger_class):
    """Test logging audit event with additional details."""
    mock_logger = Mock()
    mock_logger_class.return_value = mock_logger
    
    logger = AuditLogger()
    logger.log_event(
        event_type="blueprint_published",
        user_id="user-123",
        resource_type="blueprint",
        resource_id="bp-1",
        details={"version": "1.0.0"},
    )
    
    call_kwargs = mock_logger.info.call_args[1]
    assert call_kwargs["version"] == "1.0.0"
    assert call_kwargs["resource_id"] == "bp-1"


@pytest.mark.unit
@patch('agent_factory.security.audit._audit_logger')
def test_audit_log_function(mock_audit_logger):
    """Test audit_log convenience function."""
    Mock()
    mock_audit_logger.log_event = Mock()
    
    audit_log(
        event_type="test_event",
        user_id="user-123",
        success=True,
    )
    
    assert mock_audit_logger.log_event.called
    call_args = mock_audit_logger.log_event.call_args[1]
    assert call_args["event_type"] == "test_event"
    assert call_args["user_id"] == "user-123"


@pytest.mark.unit
@patch('agent_factory.security.audit._audit_logger')
def test_audit_log_failure(mock_audit_logger):
    """Test logging a failed action."""
    mock_audit_logger.log_event = Mock()
    
    audit_log(
        event_type="agent_delete",
        user_id="user-123",
        resource_id="agent-1",
        action="delete",
        success=False,
        details={"error": "Permission denied"},
    )
    
    call_args = mock_audit_logger.log_event.call_args[1]
    assert call_args["success"] is False
    assert call_args["details"]["error"] == "Permission denied"
