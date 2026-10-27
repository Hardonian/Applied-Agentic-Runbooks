"""Tests for signed enterprise webhook delivery."""

import asyncio
import hashlib
import hmac
import json

import httpx
import pytest

from agent_factory.enterprise import webhooks


@pytest.fixture(autouse=True)
def clean_webhooks():
    webhooks._webhooks.clear()
    yield
    webhooks._webhooks.clear()


def test_register_webhook_requires_https():
    with pytest.raises(ValueError, match="HTTPS"):
        webhooks.register_webhook("http://hooks.example.test/event", ["agent.completed"])


def test_register_webhook_deduplicates_events_and_hides_secret():
    registered = webhooks.register_webhook(
        "https://hooks.example.test/event",
        ["agent.completed", "agent.completed"],
        tenant_id="tenant-1",
        secret="signing-secret",
    )

    listed = webhooks.list_webhooks("tenant-1")
    assert registered["events"] == ["agent.completed"]
    assert listed[0]["id"] == registered["id"]
    assert "secret" not in listed[0]


def test_trigger_webhook_signs_and_retries_server_errors():
    registered = webhooks.register_webhook(
        "https://hooks.example.test/event", ["agent.completed"], secret="signing-secret"
    )

    class Client:
        def __init__(self):
            self.calls = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, *, content, headers):
            self.calls.append((url, content, headers))
            status = 500 if len(self.calls) == 1 else 204
            return httpx.Response(status, request=httpx.Request("POST", url))

    client = Client()
    results = asyncio.run(
        webhooks.trigger_webhook(
            "agent.completed", {"agent_id": "a-1"}, client_factory=lambda: client
        )
    )

    assert results == [
        {"webhook_id": registered["id"], "status": "delivered", "attempts": 2, "status_code": 204}
    ]
    body = client.calls[-1][1]
    signature = hmac.new(b"signing-secret", body, hashlib.sha256).hexdigest()
    assert client.calls[-1][2]["X-Agent-Factory-Signature"] == f"sha256={signature}"
    assert json.loads(body)["event"] == "agent.completed"
