"""
Async Streaming & Event Runtime for Agent Factory.

Provides unified streaming abstractions with:
- Token-level delta streams
- Reasoning trace streaming (<think> blocks and native thinking parts)
- Tool call previews and execution progress
- Server-Sent Events (SSE) formatter for HTTP/FastAPI streaming endpoints
- WebSocket event frame serialization
"""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StreamEventType(str, Enum):
    TOKEN = "token"  # nosec B105 -- enum member value for a stream event kind, not a credential
    REASONING = "reasoning"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_PROGRESS = "tool_call_progress"
    TOOL_CALL_COMPLETE = "tool_call_complete"
    AGENT_HANDOFF = "agent_handoff"
    ERROR = "error"
    DONE = "done"


@dataclass
class AgentStreamEvent:
    """Standardized event emitted during agent streaming execution."""

    event: StreamEventType
    data: Any
    agent_id: str | None = None
    step_id: str | None = None
    timestamp: float = field(
        default_factory=lambda: (
            asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0.0
        )
    )

    def to_sse(self) -> str:
        """Format as Server-Sent Event (SSE) message."""
        payload = json.dumps(
            {
                "type": self.event.value,
                "data": self.data,
                "agent_id": self.agent_id,
                "step_id": self.step_id,
            }
        )
        return f"event: {self.event.value}\ndata: {payload}\n\n"

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for WebSocket frames."""
        return {
            "type": self.event.value,
            "data": self.data,
            "agent_id": self.agent_id,
            "step_id": self.step_id,
        }


class StreamingAgentRuntime:
    """
    Manages async streaming generation, reasoning trace extraction,
    and event dispatching.
    """

    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size

    async def stream_tokens(
        self,
        full_text: str,
        reasoning: str | None = None,
        chunk_size: int = 4,
        delay_seconds: float = 0.01,
        agent_id: str | None = None,
    ) -> AsyncIterator[AgentStreamEvent]:
        """
        Simulate or relay token streaming with reasoning extraction.
        """
        # First stream reasoning tokens if present
        if reasoning:
            for i in range(0, len(reasoning), chunk_size * 2):
                chunk = reasoning[i : i + (chunk_size * 2)]
                yield AgentStreamEvent(
                    event=StreamEventType.REASONING,
                    data={"reasoning_delta": chunk},
                    agent_id=agent_id,
                )
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)

        # Stream content tokens
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i : i + chunk_size]
            yield AgentStreamEvent(
                event=StreamEventType.TOKEN,
                data={"delta": chunk},
                agent_id=agent_id,
            )
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

        yield AgentStreamEvent(
            event=StreamEventType.DONE,
            data={"final_text": full_text, "reasoning": reasoning},
            agent_id=agent_id,
        )
