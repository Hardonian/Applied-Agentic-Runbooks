"""Signed webhook delivery for enterprise integrations.

Registration is process-local for the current deployment profile. Production
deployments must provide durable registration storage before enabling this
feature; delivery itself is deliberately signed, bounded, and observable.
"""

import asyncio
import hashlib
import hmac
import json
import os
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from agent_factory.security.audit import audit_log

MAX_DELIVERY_ATTEMPTS = 3
DELIVERY_TIMEOUT_SECONDS = 10.0


class Webhook:
    """Registered outbound webhook definition (never serializes its secret)."""

    def __init__(
        self,
        id: str,
        url: str,
        events: list[str],
        secret: str | None = None,
        tenant_id: str | None = None,
    ):
        self.id = id
        self.url = url
        self.events = events
        self.secret = secret
        self.tenant_id = tenant_id
        self.created_at = datetime.now(timezone.utc)


_webhooks: dict[str, Webhook] = {}


def _validate_webhook_url(url: str) -> None:
    parsed = urlparse(url)
    allow_insecure = os.getenv("ALLOW_INSECURE_WEBHOOKS", "false").lower() == "true"
    if parsed.scheme not in ({"https", "http"} if allow_insecure else {"https"}):
        raise ValueError("Webhook URLs must use HTTPS")
    if not parsed.hostname:
        raise ValueError("Webhook URL must include a host")


def register_webhook(
    url: str,
    events: list[str],
    tenant_id: str | None = None,
    secret: str | None = None,
) -> dict[str, Any]:
    """Register a validated endpoint for one or more event types."""
    _validate_webhook_url(url)
    event_names = sorted({event.strip() for event in events if event and event.strip()})
    if not event_names:
        raise ValueError("At least one webhook event is required")

    webhook_id = str(uuid.uuid4())
    webhook = Webhook(
        id=webhook_id,
        url=url,
        events=event_names,
        secret=secret,
        tenant_id=tenant_id,
    )
    _webhooks[webhook_id] = webhook
    audit_log(
        event_type="webhook_registered",
        resource_type="webhook",
        resource_id=webhook_id,
        action="create",
        details={"tenant_id": tenant_id, "event_count": len(event_names)},
    )
    return {"id": webhook_id, "url": url, "events": event_names, "status": "registered"}


def _delivery_payload(event_type: str, payload: dict[str, Any]) -> tuple[bytes, str]:
    timestamp = datetime.now(timezone.utc).isoformat()
    body = json.dumps(
        {"event": event_type, "payload": payload, "timestamp": timestamp},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return body, timestamp


def _delivery_headers(webhook: Webhook, body: bytes, timestamp: str) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Agent-Factory-Event": "webhook",
        "X-Agent-Factory-Timestamp": timestamp,
    }
    if webhook.secret:
        digest = hmac.new(webhook.secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        headers["X-Agent-Factory-Signature"] = f"sha256={digest}"
    return headers


async def trigger_webhook(
    event_type: str,
    payload: dict[str, Any],
    tenant_id: str | None = None,
    *,
    max_attempts: int = MAX_DELIVERY_ATTEMPTS,
    client_factory: Callable[[], httpx.AsyncClient] | None = None,
) -> list[dict[str, Any]]:
    """Deliver an event to matching hooks with bounded retry/backoff.

    The return value is a per-webhook delivery record suitable for a worker or
    durable queue to persist. Secrets and full payloads are never logged.
    """
    if not event_type:
        raise ValueError("event_type is required")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    matching_webhooks = [
        webhook
        for webhook in _webhooks.values()
        if event_type in webhook.events and (tenant_id is None or webhook.tenant_id == tenant_id)
    ]
    if not matching_webhooks:
        return []

    results: list[dict[str, Any]] = []
    factory = client_factory or (lambda: httpx.AsyncClient(timeout=DELIVERY_TIMEOUT_SECONDS))
    async with factory() as client:
        for webhook in matching_webhooks:
            body, timestamp = _delivery_payload(event_type, payload)
            headers = _delivery_headers(webhook, body, timestamp)
            last_error: str | None = None
            response_status: int | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    response = await client.post(webhook.url, content=body, headers=headers)
                    response_status = response.status_code
                    if response.status_code < 400:
                        result = {
                            "webhook_id": webhook.id,
                            "status": "delivered",
                            "attempts": attempt,
                            "status_code": response.status_code,
                        }
                        audit_log(
                            event_type="webhook_delivered",
                            resource_type="webhook",
                            resource_id=webhook.id,
                            action="deliver",
                            details={"event_type": event_type, **result},
                        )
                        results.append(result)
                        break
                    last_error = f"HTTP {response.status_code}"
                    if response.status_code < 500 and response.status_code != 429:
                        break
                except httpx.HTTPError as exc:
                    last_error = type(exc).__name__

                if attempt < max_attempts:
                    await asyncio.sleep(0.1 * (2 ** (attempt - 1)))
            else:
                pass

            if not results or results[-1].get("webhook_id") != webhook.id:
                result = {
                    "webhook_id": webhook.id,
                    "status": "failed",
                    "attempts": (
                        max_attempts
                        if response_status is None or response_status >= 500
                        else attempt
                    ),
                    "status_code": response_status,
                    "error": last_error or "delivery failed",
                }
                audit_log(
                    event_type="webhook_delivery_failed",
                    resource_type="webhook",
                    resource_id=webhook.id,
                    action="deliver",
                    success=False,
                    details={"event_type": event_type, **result},
                )
                results.append(result)
    return results


def list_webhooks(tenant_id: str | None = None) -> list[dict[str, Any]]:
    """List registrations without exposing webhook secrets."""
    return [
        {
            "id": webhook.id,
            "url": webhook.url,
            "events": webhook.events,
            "tenant_id": webhook.tenant_id,
            "created_at": webhook.created_at.isoformat(),
        }
        for webhook in _webhooks.values()
        if tenant_id is None or webhook.tenant_id == tenant_id
    ]
