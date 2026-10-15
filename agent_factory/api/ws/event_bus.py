"""Bounded resumable pub/sub with optional Redis Streams cross-pod transport."""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventBus:
    """Fan out versioned events while isolating and measuring slow consumers."""

    queue_size: int = 256
    history_size: int = 1000
    backend: str = field(default_factory=lambda: os.getenv("EVENT_BUS_BACKEND", "memory"))
    _subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = field(default_factory=dict)
    _history: dict[str, deque[dict[str, Any]]] = field(default_factory=dict)
    _sequences: dict[str, int] = field(default_factory=dict)
    _dropped_events: int = 0
    _redis_tasks: dict[str, asyncio.Task[None]] = field(default_factory=dict)
    _instance_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    _redis: Any = None

    def subscribe(
        self, topic: str, after_sequence: int | None = None
    ) -> asyncio.Queue[dict[str, Any]]:
        """Register a queue and replay retained events after an optional cursor."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.queue_size)
        self._subscribers.setdefault(topic, set()).add(queue)
        self._set_subscriber_metric()
        if after_sequence is not None:
            for event in self._history.get(topic, ()):
                if int(event.get("sequence", 0)) > after_sequence:
                    if queue.full():
                        break
                    queue.put_nowait(dict(event))
        if self.backend == "redis" and topic not in self._redis_tasks:
            try:
                loop = asyncio.get_running_loop()
                self._redis_tasks[topic] = loop.create_task(self._consume_redis(topic))
            except RuntimeError:
                pass
        return queue

    def unsubscribe(self, topic: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subscribers = self._subscribers.get(topic)
        if subscribers is not None:
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(topic, None)
                task = self._redis_tasks.pop(topic, None)
                if task:
                    task.cancel()
        self._set_subscriber_metric()

    async def publish(self, topic: str, event: dict[str, Any]) -> dict[str, Any]:
        """Publish locally and to Redis Streams, returning the canonical envelope."""
        sequence = self._sequences.get(topic, 0) + 1
        self._sequences[topic] = sequence
        envelope = dict(event)
        envelope.setdefault("schema_version", "1.0")
        envelope.setdefault("topic", topic)
        envelope.setdefault("timestamp", time.time())
        envelope.setdefault("sequence", sequence)
        envelope.setdefault("event_id", f"{topic}:{sequence}")
        envelope.setdefault("origin", self._instance_id)
        try:
            from agent_factory.monitoring.tracing import get_trace_context

            envelope.update(
                {key: value for key, value in get_trace_context().items() if key not in envelope}
            )
        except ImportError:
            pass
        self._retain(topic, envelope)
        self._fanout(topic, envelope)
        if self.backend == "redis":
            redis = await self._redis_client()
            if redis is not None:
                import json

                await redis.xadd(
                    f"agent-factory:events:{topic}",
                    {"event": json.dumps(envelope, separators=(",", ":"), default=str)},
                    maxlen=self.history_size,
                    approximate=True,
                )
        return envelope

    def _retain(self, topic: str, event: dict[str, Any]) -> None:
        history = self._history.setdefault(topic, deque(maxlen=self.history_size))
        history.append(dict(event))

    def _fanout(self, topic: str, envelope: dict[str, Any]) -> None:
        queues = set(self._subscribers.get(topic, set())) | set(self._subscribers.get("*", set()))
        for queue in queues:
            if queue.full():
                try:
                    queue.get_nowait()
                    queue.task_done()
                    self._dropped_events += 1
                    try:
                        from agent_factory.monitoring.metrics import MetricsCollector

                        MetricsCollector.record_websocket_drop()
                    except ImportError:
                        pass
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(dict(envelope))

    async def _redis_client(self) -> Any:
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
            )
            await self._redis.ping()
        except Exception:  # noqa: BLE001
            self._redis = None
        return self._redis

    async def _consume_redis(self, topic: str) -> None:
        import json

        last_id = "$"
        while topic in self._subscribers:
            redis = await self._redis_client()
            if redis is None:
                await asyncio.sleep(1)
                continue
            try:
                entries = await redis.xread(
                    {f"agent-factory:events:{topic}": last_id}, block=1000, count=100
                )
                for _stream, messages in entries:
                    for message_id, fields in messages:
                        last_id = message_id
                        envelope = json.loads(fields["event"])
                        if envelope.get("origin") == self._instance_id:
                            continue
                        sequence = self._sequences.get(topic, 0) + 1
                        self._sequences[topic] = sequence
                        envelope["sequence"] = sequence
                        envelope["event_id"] = f"{topic}:{sequence}"
                        self._retain(topic, envelope)
                        self._fanout(topic, envelope)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                self._redis = None
                await asyncio.sleep(1)

    def replay(self, topic: str, after_sequence: int = 0) -> list[dict[str, Any]]:
        """Return retained envelopes newer than a cursor."""
        return [
            dict(event)
            for event in self._history.get(topic, ())
            if int(event.get("sequence", 0)) > after_sequence
        ]

    @property
    def subscriber_count(self) -> int:
        return sum(len(items) for items in self._subscribers.values())

    @property
    def dropped_events(self) -> int:
        return self._dropped_events

    def stats(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "subscribers": self.subscriber_count,
            "dropped_events": self._dropped_events,
            "topics": {topic: len(events) for topic, events in self._history.items()},
        }

    def _set_subscriber_metric(self) -> None:
        try:
            from agent_factory.monitoring.metrics import MetricsCollector

            MetricsCollector.set_websocket_subscribers(self.subscriber_count)
        except ImportError:
            pass


event_bus = EventBus()
