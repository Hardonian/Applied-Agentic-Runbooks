"""
Tests for MCPWall zero-trust security and human approval gates.
"""

import os

import pytest

from agent_factory.security.mcpwall import (
    MCPWall,
)


@pytest.mark.unit
def test_mcpwall_denylist_and_containment():
    """Verify MCPWall blocks explicit denylist tools and out-of-boundary paths."""
    firewall = MCPWall(path_roots=[os.getcwd()])

    # 1. Denied tool
    v_denied = firewall.validate_tool_call("delete_database", {})
    assert v_denied.allowed is False
    assert "explicitly denied" in v_denied.reason

    # 2. Out-of-boundary path traversal attempt
    v_escape = firewall.validate_tool_call(
        "read_file",
        {"filepath": "C:\\Windows\\System32\\drivers\\etc\\hosts"},
    )
    assert v_escape.allowed is False
    assert "escapes authorized root" in v_escape.reason


@pytest.mark.unit
def test_mcpwall_human_gate_and_replay_prevention():
    """Verify destructive operations trigger cryptographic challenge and block replays."""
    firewall = MCPWall()

    args = {"filename": "audit.txt", "content": "Critical log payload"}

    # First invocation without ticket -> triggers human gate
    v1 = firewall.validate_tool_call("write_file", args)
    assert v1.allowed is False
    assert v1.requires_approval is True
    assert v1.ticket is not None
    ticket_id = v1.ticket.ticket_id

    # Call with ticket before operator approves -> blocked
    v_unapproved = firewall.validate_tool_call("write_file", args, approval_ticket_id=ticket_id)
    assert v_unapproved.allowed is False
    assert "not yet been approved" in v_unapproved.reason

    # Approve ticket
    assert firewall.approve_ticket(ticket_id, approver="SecurityOperator") is True

    # Call with approved ticket -> succeeds!
    v_success = firewall.validate_tool_call("write_file", args, approval_ticket_id=ticket_id)
    assert v_success.allowed is True
    assert v_success.sanitized_args == args

    # Attempt replay with consumed ticket -> blocked!
    v_replay = firewall.validate_tool_call("write_file", args, approval_ticket_id=ticket_id)
    assert v_replay.allowed is False
    assert "already consumed" in v_replay.reason
