"""Bi-directional live execution and arena WebSocket routes."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agent_factory.api.ws.event_bus import event_bus
from agent_factory.evaluation.arena import ArenaRunner

router = APIRouter()
approval_decisions: dict[str, dict[str, Any]] = {}


async def _send_events(websocket: WebSocket, topic: str) -> None:
    queue = event_bus.subscribe(topic)
    try:
        while True:
            await websocket.send_json(await queue.get())
            queue.task_done()
    finally:
        event_bus.unsubscribe(topic, queue)


async def _emit_offline_tokens(prompt: str) -> None:
    response = f"Offline deterministic response: {prompt.strip()}"
    stream_id = hashlib.sha256(f"{prompt}:{time.time_ns()}".encode()).hexdigest()[:16]
    await event_bus.publish("stream", {"type": "stream.started", "stream_id": stream_id})
    for index, token in enumerate(response.split()):
        await event_bus.publish(
            "stream",
            {"type": "token.chunk", "stream_id": stream_id, "index": index, "token": token + " "},
        )
        await asyncio.sleep(0)
    await event_bus.publish("stream", {"type": "stream.completed", "stream_id": stream_id})


async def _handle_control(websocket: WebSocket, message: dict[str, Any], topic: str) -> None:
    message_type = str(message.get("type", ""))
    if message_type == "ping":
        await websocket.send_json({"type": "pong", "timestamp": time.time()})
    elif message_type in {"approval.approve", "approval.deny"}:
        ticket_id = str(message.get("ticket_id", ""))
        decision = "approved" if message_type.endswith("approve") else "denied"
        approval_decisions[ticket_id] = {
            "decision": decision,
            "approver": str(message.get("approver", "studio-operator")),
            "timestamp": time.time(),
        }
        await event_bus.publish(
            topic,
            {"type": "approval.resolved", "ticket_id": ticket_id, **approval_decisions[ticket_id]},
        )
    elif message_type == "stream.prompt":
        await _emit_offline_tokens(str(message.get("prompt", "")))
    elif message_type == "arena.run":
        requested = message.get("suites")
        suites = requested if isinstance(requested, list) else None
        runner = ArenaRunner()

        async def sink(event: dict[str, Any]) -> None:
            await event_bus.publish("arena", event)

        asyncio.create_task(runner.run(suites=suites, event_sink=sink))
    else:
        await websocket.send_json(
            {"type": "error", "code": "unsupported_message", "message": message_type}
        )


async def _serve(websocket: WebSocket, topic: str) -> None:
    await websocket.accept()
    requested_topic = websocket.query_params.get("topic", topic)
    sender = asyncio.create_task(_send_events(websocket, requested_topic))
    await websocket.send_json({"type": "connected", "topic": requested_topic})
    try:
        while True:
            packet = await websocket.receive()
            if packet.get("text") == "ping":
                message = {"type": "ping"}
            elif packet.get("text"):
                message = json.loads(packet["text"])
            else:
                continue
            await _handle_control(websocket, message, requested_topic)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        sender.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sender


@router.websocket("/stream")
async def stream_socket(websocket: WebSocket) -> None:
    """Stream token, tool, tree, PCAP, and velocity events bi-directionally."""
    await _serve(websocket, "stream")


@router.websocket("/arena")
async def arena_socket(websocket: WebSocket) -> None:
    """Run gauntlets and stream suite/leaderboard progress."""
    await _serve(websocket, "arena")
