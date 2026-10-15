"""Authenticated, resumable bi-directional execution and Arena WebSockets."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from agent_factory.api.ws.event_bus import event_bus
from agent_factory.database.models import User as UserModel
from agent_factory.database.session import SessionLocal
from agent_factory.evaluation.arena.service import arena_service
from agent_factory.security.approval import approval_authority
from agent_factory.security.auth import verify_token

router = APIRouter()


async def _send_events(websocket: WebSocket, topic: str, after_sequence: int | None = None) -> None:
    queue = event_bus.subscribe(topic, after_sequence)
    try:
        while True:
            await websocket.send_json(await queue.get())
            queue.task_done()
    finally:
        event_bus.unsubscribe(topic, queue)


async def _emit_offline_tokens(prompt: str, topic: str = "stream") -> None:
    response = f"Offline deterministic response: {prompt.strip()}"
    stream_id = hashlib.sha256(f"{prompt}:{time.time_ns()}".encode()).hexdigest()[:16]
    await event_bus.publish(topic, {"type": "stream.started", "stream_id": stream_id})
    for index, token in enumerate(response.split()):
        await event_bus.publish(
            topic,
            {"type": "token.chunk", "stream_id": stream_id, "index": index, "token": token + " "},
        )
        await asyncio.sleep(0)
    await event_bus.publish(topic, {"type": "stream.completed", "stream_id": stream_id})


def _principal(websocket: WebSocket) -> dict[str, Any]:
    token = websocket.query_params.get("token")
    testing = os.getenv("TESTING", "false").lower() == "true"
    if not token:
        return {
            "user_id": "test-operator" if testing else None,
            "tenant_id": "public",
            "roles": {"operator"} if testing else set(),
        }
    token_data = verify_token(token)
    with SessionLocal() as session:
        user = session.query(UserModel).filter(UserModel.id == token_data.user_id).first()
        if user is None or not user.is_active:
            return {"user_id": None, "tenant_id": "public", "roles": set()}
        return {
            "user_id": user.id,
            "tenant_id": user.tenant_id or "public",
            "roles": set(user.roles or []),
        }


def _origin_allowed(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin")
    if not origin:
        return True
    allowed = {
        item.strip()
        for item in os.getenv(
            "WS_ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:8000,http://localhost:8080",
        ).split(",")
        if item.strip()
    }
    return origin in allowed


async def _handle_control(
    websocket: WebSocket,
    message: dict[str, Any],
    topic: str,
    principal: dict[str, Any],
) -> None:
    message_type = str(message.get("type", ""))
    if message_type == "ping":
        await websocket.send_json({"type": "pong", "timestamp": time.time(), "topic": topic})
    elif message_type in {"approval.approve", "approval.deny"}:
        if not principal["user_id"]:
            await websocket.send_json({"type": "error", "code": "authentication_required"})
            return
        decision = "approved" if message_type.endswith("approve") else "denied"
        try:
            receipt = await asyncio.to_thread(
                approval_authority.resolve,
                str(message.get("ticket_id", "")),
                decision,
                str(principal["user_id"]),
                tenant_id=str(principal["tenant_id"]),
                roles=set(principal["roles"]),
                reason=str(message.get("reason", "")),
            )
            await event_bus.publish(
                f"approvals:{principal['tenant_id']}",
                {"type": "approval.resolved", "data": asdict(receipt)},
            )
        except (KeyError, ValueError, PermissionError) as exc:
            await websocket.send_json(
                {"type": "error", "code": "approval_rejected", "message": str(exc)}
            )
    elif message_type == "stream.prompt":
        await _emit_offline_tokens(str(message.get("prompt", "")), topic)
    elif message_type == "arena.run":
        request = {
            "suites": message.get("suites"),
            "concurrency": int(message.get("concurrency", 32)),
            "trials": int(message.get("trials", 1)),
            "mode": str(message.get("mode", "deterministic")),
            "timeout_seconds": float(message.get("timeout_seconds", 900)),
        }
        record = await arena_service.submit(
            request,
            tenant_id=str(principal["tenant_id"]),
            created_by=principal["user_id"],
        )
        await websocket.send_json({"type": "arena.accepted", "data": record})
    elif message_type == "arena.cancel":
        cancelled = await arena_service.cancel(
            str(message.get("run_id", "")), str(principal["tenant_id"])
        )
        await websocket.send_json({"type": "arena.cancel.result", "cancelled": cancelled})
    else:
        await websocket.send_json(
            {"type": "error", "code": "unsupported_message", "message": message_type}
        )


async def _serve(websocket: WebSocket, topic: str) -> None:
    if not _origin_allowed(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Origin not allowed")
        return
    principal = _principal(websocket)
    requested_topic = websocket.query_params.get("topic", topic)
    if requested_topic.startswith("approvals:") and not principal["user_id"]:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required"
        )
        return
    cursor_value = websocket.query_params.get("cursor")
    cursor = int(cursor_value) if cursor_value and cursor_value.isdigit() else None
    await websocket.accept()
    sender = asyncio.create_task(_send_events(websocket, requested_topic, cursor))
    await websocket.send_json(
        {
            "type": "connected",
            "topic": requested_topic,
            "cursor": cursor,
            "backend": event_bus.backend,
        }
    )
    try:
        while True:
            packet = await websocket.receive()
            if packet.get("text") == "ping":
                message = {"type": "ping"}
            elif packet.get("text"):
                message = json.loads(packet["text"])
            else:
                continue
            await _handle_control(websocket, message, requested_topic, principal)
    except (WebSocketDisconnect, RuntimeError, json.JSONDecodeError):
        pass
    finally:
        sender.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sender


@router.websocket("/stream")
async def stream_socket(websocket: WebSocket) -> None:
    await _serve(websocket, "stream")


@router.websocket("/arena")
async def arena_socket(websocket: WebSocket) -> None:
    await _serve(websocket, "arena")
