"""Webhook system for enterprise integrations."""

from datetime import datetime
from typing import Any

import httpx


class Webhook:
    """Webhook model."""

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
        self.created_at = datetime.utcnow()


# In-memory webhook storage (in production, use database)
_webhooks: dict[str, Webhook] = {}


def register_webhook(
    url: str, events: list[str], tenant_id: str | None = None, secret: str | None = None
) -> dict[str, Any]:
    """
    Register webhook.

    Args:
        url: Webhook URL
        events: List of events to subscribe to
        tenant_id: Tenant ID (optional)
        secret: Webhook secret for signing

    Returns:
        Webhook registration info
    """
    import uuid

    webhook_id = str(uuid.uuid4())
    webhook = Webhook(id=webhook_id, url=url, events=events, secret=secret, tenant_id=tenant_id)

    _webhooks[webhook_id] = webhook

    return {"id": webhook_id, "url": url, "events": events, "status": "registered"}


async def trigger_webhook(event_type: str, payload: dict[str, Any], tenant_id: str | None = None):
    """
    Trigger webhooks for event.

    Args:
        event_type: Event type
        payload: Event payload
        tenant_id: Tenant ID (optional filter)
    """
    matching_webhooks = [
        wh
        for wh in _webhooks.values()
        if event_type in wh.events and (tenant_id is None or wh.tenant_id == tenant_id)
    ]

    async with httpx.AsyncClient() as client:
        for webhook in matching_webhooks:
            try:
                # Sign payload if secret provided
                headers = {"Content-Type": "application/json"}
                if webhook.secret:
                    # In production, add HMAC signature
                    headers["X-Webhook-Signature"] = "signature"

                response = await client.post(
                    webhook.url,
                    json={
                        "event": event_type,
                        "payload": payload,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code >= 400:
                    # Log failed webhook
                    pass
            except Exception:
                # Log webhook failure
                pass


def list_webhooks(tenant_id: str | None = None) -> list[dict[str, Any]]:
    """
    List registered webhooks.

    Args:
        tenant_id: Tenant ID filter (optional)

    Returns:
        List of webhooks
    """
    webhooks = [wh for wh in _webhooks.values() if tenant_id is None or wh.tenant_id == tenant_id]

    return [
        {
            "id": wh.id,
            "url": wh.url,
            "events": wh.events,
            "tenant_id": wh.tenant_id,
            "created_at": wh.created_at.isoformat(),
        }
        for wh in webhooks
    ]
