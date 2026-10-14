"""Bounded asynchronous in-process pub/sub for live Studio telemetry."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventBus:
    """Fan out JSON events while isolating slow WebSocket consumers."""

    queue_size: int = 256
    _subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = field(default_factory=dict)

    def subscribe(self, topic: str) -> asyncio.Queue[dict[str, Any]]:
        """Register a bounded queue for a topic."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.queue_size)
        self._subscribers.setdefault(topic, set()).add(queue)
        return queue

    def unsubscribe(self, topic: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Remove a subscriber without affecting other clients."""
        subscribers = self._subscribers.get(topic)
        if subscribers is not None:
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(topic, None)

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        """Publish an event, dropping the oldest item only for lagging consumers."""
        envelope = dict(event)
        envelope.setdefault("topic", topic)
        envelope.setdefault("timestamp", time.time())
        queues = set(self._subscribers.get(topic, set())) | set(
            self._subscribers.get("*", set())
        )
        for queue in queues:
            if queue.full():
                try:
                    queue.get_nowait()
                    queue.task_done()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(envelope)

    @property
    def subscriber_count(self) -> int:
        """Return the total number of active subscriptions."""
        return sum(len(items) for items in self._subscribers.values())


event_bus = EventBus()
