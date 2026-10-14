"""Tests for WebSocket bi-directional streaming and event bus."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from agent_factory.api.main import app
from agent_factory.api.ws.event_bus import event_bus


@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    """Verify in-process async event bus broadcasts to subscribers."""
    received = []

    async def listener(event: dict):
        received.append(event)

    queue = event_bus.subscribe("test-topic")
    try:
        await event_bus.publish("test-topic", {"msg": "hello-agent"})
        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert event["msg"] == "hello-agent"
    finally:
        event_bus.unsubscribe("test-topic", queue)


def test_websocket_stream_connection():
    """Verify WebSocket endpoint connection and telemetry stream handshake."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/stream?topic=telemetry") as websocket:
        init_data = websocket.receive_json()
        assert init_data["type"] == "connected"
        assert init_data["topic"] == "telemetry"

        websocket.send_json({"type": "ping"})
        reply = websocket.receive_json()
        assert reply["type"] == "pong"
        assert "timestamp" in reply
