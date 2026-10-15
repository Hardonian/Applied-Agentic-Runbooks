"""Authoritative, tenant-bound MCPWall approval authority and signed receipts."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, ClassVar

from agent_factory.database.models import ApprovalTicket
from agent_factory.database.session import Base, SessionLocal, engine
from agent_factory.security.mcpwall import HumanApprovalTicket


@dataclass(frozen=True)
class ApprovalReceipt:
    ticket_id: str
    tenant_id: str
    decision: str
    approver: str
    decided_at: float
    request_hash: str
    signature: str


class ApprovalAuthority:
    """Persist and resolve tickets with RBAC, separation of duty, TTL, and HMAC receipts."""

    allowed_roles: ClassVar[set[str]] = {"operator", "security", "admin"}

    def __init__(self, signing_key: str | None = None) -> None:
        configured = (
            signing_key
            or os.getenv("MCPWALL_APPROVAL_SIGNING_KEY")
            or os.getenv("JWT_SECRET_KEY", "development-approval-key")
        )
        self.signing_key = (configured or "development-approval-key").encode("utf-8")
        Base.metadata.create_all(bind=engine, tables=[ApprovalTicket.__table__])

    def create(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        request_hash: str,
        expires_at: float,
        *,
        tenant_id: str = "public",
        requested_by: str | None = None,
    ) -> HumanApprovalTicket:
        ticket_id = f"mcp-gate-{uuid.uuid4().hex[:12]}"
        created = datetime.now(timezone.utc).replace(tzinfo=None)
        record = ApprovalTicket(
            id=ticket_id,
            tenant_id=tenant_id,
            tool_name=tool_name,
            request_hash=request_hash,
            arguments=arguments,
            requested_by=requested_by,
            status="pending",
            created_at=created,
            expires_at=datetime.fromtimestamp(expires_at, timezone.utc).replace(tzinfo=None),
        )
        with SessionLocal() as session:
            session.add(record)
            session.commit()
        return HumanApprovalTicket(
            ticket_id=ticket_id,
            tool_name=tool_name,
            request_hash=request_hash,
            created_at=created.replace(tzinfo=timezone.utc).timestamp(),
            expires_at=expires_at,
            tenant_id=tenant_id,
        )

    def get(self, ticket_id: str, tenant_id: str = "public") -> HumanApprovalTicket | None:
        with SessionLocal() as session:
            record = (
                session.query(ApprovalTicket)
                .filter(ApprovalTicket.id == ticket_id, ApprovalTicket.tenant_id == tenant_id)
                .first()
            )
            if record is None:
                return None
            if not all(
                (
                    record.id,
                    record.tool_name,
                    record.request_hash,
                    record.created_at,
                    record.expires_at,
                    record.tenant_id,
                    record.status,
                )
            ):
                raise RuntimeError("Persisted approval ticket is incomplete")
            assert record.created_at is not None
            assert record.expires_at is not None
            return HumanApprovalTicket(
                ticket_id=str(record.id),
                tool_name=str(record.tool_name),
                request_hash=str(record.request_hash),
                created_at=record.created_at.replace(tzinfo=timezone.utc).timestamp(),
                expires_at=record.expires_at.replace(tzinfo=timezone.utc).timestamp(),
                consumed=record.consumed_at is not None,
                approved_by=record.decided_by if record.status == "approved" else None,
                tenant_id=str(record.tenant_id),
                decision=str(record.status),
            )

    def resolve(
        self,
        ticket_id: str,
        decision: str,
        approver: str,
        *,
        tenant_id: str = "public",
        roles: set[str] | None = None,
        reason: str = "",
    ) -> ApprovalReceipt:
        normalized = decision.lower()
        if normalized not in {"approved", "denied"}:
            raise ValueError("Decision must be approved or denied")
        if not (roles or set()) & self.allowed_roles:
            raise PermissionError("Operator role is required")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with SessionLocal() as session:
            record = (
                session.query(ApprovalTicket)
                .filter(ApprovalTicket.id == ticket_id, ApprovalTicket.tenant_id == tenant_id)
                .with_for_update()
                .first()
            )
            if record is None:
                raise KeyError("Approval ticket not found")
            if not all((record.id, record.tenant_id, record.request_hash, record.expires_at)):
                raise RuntimeError("Persisted approval ticket is incomplete")
            assert record.expires_at is not None
            if record.status != "pending":
                raise ValueError("Approval ticket has already been resolved")
            if record.expires_at < now:
                record.status = "expired"
                session.commit()
                raise ValueError("Approval ticket expired")
            if record.requested_by and record.requested_by == approver:
                raise PermissionError("Requester cannot approve their own operation")
            decided_at = now.replace(tzinfo=timezone.utc).timestamp()
            signature = self._sign(
                str(record.id),
                str(record.tenant_id),
                normalized,
                approver,
                decided_at,
                str(record.request_hash),
            )
            record.status = normalized
            record.decided_at = now
            record.decided_by = approver
            record.decision_reason = reason
            record.receipt_signature = signature
            session.commit()
            from agent_factory.monitoring.metrics import MetricsCollector

            MetricsCollector.record_approval(normalized)
            return ApprovalReceipt(
                ticket_id=str(record.id),
                tenant_id=str(record.tenant_id),
                decision=normalized,
                approver=approver,
                decided_at=decided_at,
                request_hash=str(record.request_hash),
                signature=signature,
            )

    def consume(self, ticket_id: str, tenant_id: str = "public") -> bool:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with SessionLocal() as session:
            record = (
                session.query(ApprovalTicket)
                .filter(ApprovalTicket.id == ticket_id, ApprovalTicket.tenant_id == tenant_id)
                .with_for_update()
                .first()
            )
            if record is None or record.status != "approved" or record.consumed_at is not None:
                return False
            record.consumed_at = now
            session.commit()
            return True

    def verify_receipt(self, receipt: ApprovalReceipt | dict[str, Any]) -> bool:
        data = asdict(receipt) if isinstance(receipt, ApprovalReceipt) else receipt
        expected = self._sign(
            str(data["ticket_id"]),
            str(data["tenant_id"]),
            str(data["decision"]),
            str(data["approver"]),
            float(data["decided_at"]),
            str(data["request_hash"]),
        )
        return hmac.compare_digest(expected, str(data["signature"]))

    def _sign(self, *parts: Any) -> str:
        payload = json.dumps(parts, separators=(",", ":"), default=str).encode("utf-8")
        return hmac.new(self.signing_key, payload, hashlib.sha256).hexdigest()


approval_authority = ApprovalAuthority()
