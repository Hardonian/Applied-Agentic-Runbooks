"""
MCPWall: Zero-Trust Local Policy Firewall & Human Approval Gate for Tool/MCP Execution.

Folded in from mcpwall (Hardonian/mcpwall):
- Tool allowlists and denylists
- Path root containment (preventing directory traversal / symlink escapes)
- Argument byte limits & payload sizing
- Single-use, TTL-bound, SHA-256-bound human approval gates for destructive operations
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class MCPWallSecurityError(Exception):
    """Raised when an MCP or tool invocation violates policy."""


@dataclass
class HumanApprovalTicket:
    """A cryptographic challenge required to execute destructive operations."""
    ticket_id: str
    tool_name: str
    request_hash: str
    created_at: float
    expires_at: float
    consumed: bool = False
    approved_by: str | None = None


@dataclass
class MCPWallVerdict:
    """Evaluation verdict from MCPWall."""
    allowed: bool
    reason: str
    requires_approval: bool = False
    ticket: HumanApprovalTicket | None = None
    sanitized_args: dict[str, Any] | None = None


class MCPWall:
    """
    Zero-trust policy engine protecting agent execution from unauthorized,
    destructive, or out-of-boundary tool operations.
    """

    def __init__(
        self,
        allowed_tools: set[str] | None = None,
        denied_tools: set[str] | None = None,
        destructive_tools: set[str] | None = None,
        path_roots: list[str] | None = None,
        max_request_bytes: int = 65536,
        approval_ttl_seconds: int = 300,
    ):
        self.allowed_tools = allowed_tools  # None means all non-denied allowed
        self.denied_tools = denied_tools or {"delete_database", "drop_table", "shell_exec_raw"}
        self.destructive_tools = destructive_tools or {"execute_code", "write_file", "delete_file", "transfer_funds"}
        self.path_roots = [Path(p).resolve() for p in (path_roots or [os.getcwd()])]
        self.max_request_bytes = max_request_bytes
        self.approval_ttl_seconds = approval_ttl_seconds
        self.pending_approvals: dict[str, HumanApprovalTicket] = {}

    def compute_request_hash(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Calculate canonical SHA-256 hash of tool call payload."""
        payload = {
            "tool": tool_name,
            "args": arguments,
        }
        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def request_approval(self, tool_name: str, arguments: dict[str, Any]) -> HumanApprovalTicket:
        """Create a cryptographic challenge for human gate confirmation."""
        req_hash = self.compute_request_hash(tool_name, arguments)
        ticket_id = f"mcp-gate-{uuid.uuid4().hex[:12]}"
        now = time.time()
        ticket = HumanApprovalTicket(
            ticket_id=ticket_id,
            tool_name=tool_name,
            request_hash=req_hash,
            created_at=now,
            expires_at=now + self.approval_ttl_seconds,
        )
        self.pending_approvals[ticket_id] = ticket
        return ticket

    def approve_ticket(self, ticket_id: str, approver: str = "Operator") -> bool:
        """Approve a pending human gate ticket."""
        ticket = self.pending_approvals.get(ticket_id)
        if not ticket or ticket.consumed or time.time() > ticket.expires_at:
            return False
        ticket.approved_by = approver
        return True

    def validate_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        approval_ticket_id: str | None = None,
    ) -> MCPWallVerdict:
        """
        Evaluate tool invocation against security boundary rules.
        """
        # 1. Denylist check
        if tool_name in self.denied_tools:
            return MCPWallVerdict(
                allowed=False,
                reason=f"Tool '{tool_name}' is explicitly denied by MCPWall policy.",
            )

        # 2. Allowlists check (if defined)
        if self.allowed_tools is not None and tool_name not in self.allowed_tools:
            return MCPWallVerdict(
                allowed=False,
                reason=f"Tool '{tool_name}' is not in approved allowlist.",
            )

        # 3. Request byte payload limits
        try:
            serialized = json.dumps(arguments)
            if len(serialized.encode("utf-8")) > self.max_request_bytes:
                return MCPWallVerdict(
                    allowed=False,
                    reason=f"Payload size exceeds max limit of {self.max_request_bytes} bytes.",
                )
        except (TypeError, ValueError):
            return MCPWallVerdict(allowed=False, reason="Unserializable arguments payload.")

        # 4. Path boundary containment
        for key in ["path", "filepath", "target_file", "file_path", "directory"]:
            if key in arguments and isinstance(arguments[key], str):
                target_path = Path(arguments[key]).resolve()
                is_contained = any(
                    target_path == root or root in target_path.parents
                    for root in self.path_roots
                )
                if not is_contained:
                    return MCPWallVerdict(
                        allowed=False,
                        reason=f"Path '{target_path}' escapes authorized root boundaries.",
                    )

        # 5. Destructive tool human approval gate
        if tool_name in self.destructive_tools:
            if not approval_ticket_id:
                ticket = self.request_approval(tool_name, arguments)
                return MCPWallVerdict(
                    allowed=False,
                    requires_approval=True,
                    ticket=ticket,
                    reason=f"Destructive tool '{tool_name}' requires human approval. Ticket: {ticket.ticket_id}",
                )

            ticket = self.pending_approvals.get(approval_ticket_id)
            if not ticket:
                return MCPWallVerdict(allowed=False, reason="Invalid approval ticket.")
            if ticket.consumed:
                return MCPWallVerdict(allowed=False, reason="Approval ticket already consumed (replay blocked).")
            if time.time() > ticket.expires_at:
                return MCPWallVerdict(allowed=False, reason="Approval ticket expired.")
            if not ticket.approved_by:
                return MCPWallVerdict(allowed=False, reason="Ticket has not yet been approved.")

            # Validate payload integrity against ticket hash
            expected_hash = self.compute_request_hash(tool_name, arguments)
            if ticket.request_hash != expected_hash:
                return MCPWallVerdict(
                    allowed=False,
                    reason="Tampered request: arguments do not match approval ticket hash.",
                )

            # Consume ticket (single-use invariant)
            ticket.consumed = True

        return MCPWallVerdict(
            allowed=True,
            reason="Approved by MCPWall policy.",
            sanitized_args=arguments,
        )
