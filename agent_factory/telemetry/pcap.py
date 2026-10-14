"""
AgentPCAP: Unified Packet Capture & Deterministic Pathology Debugger for Agents.

Folded in from AgentPCAP (Hardonian/AgentPCAP):
- Unified packet timeline capturing A2A, Tool, and Model frames
- Deterministic heuristic pathology detection (Zero-LLM overhead)
- Detection of Retry Storms, Ping-Pong Loops, and Token Burning Anomaly Spikes
- Exportable .apcap capture format
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class FrameType(str, Enum):
    A2A = "a2a"          # Agent-to-Agent communication
    TOOL = "tool"        # Tool invocation & result
    MODEL = "model"      # LLM inference request/response
    SYSTEM = "system"    # Lifecycle & guardrail events


class PathologyType(str, Enum):
    RETRY_STORM = "retry_storm"            # Repetitive tool failures with identical args
    PING_PONG_LOOP = "ping_pong_loop"      # Agents bouncing messages without progression
    TOKEN_BURNING = "token_burning"        # Massive token consumption with minimal output
    SLOW_DRAIN = "slow_drain"              # Latency spikes without tool execution progress


@dataclass
class PCAPFrame:
    """A single captured protocol frame in the agent communication stream."""
    frame_id: str
    timestamp: float
    frame_type: FrameType
    source: str
    destination: str
    payload: Dict[str, Any]
    tokens_used: int = 0
    duration_ms: float = 0.0
    payload_hash: str = ""

    def __post_init__(self):
        if not self.payload_hash:
            try:
                raw = json.dumps(self.payload, sort_keys=True, default=str)
            except Exception:
                raw = str(self.payload)
            self.payload_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class PathologyDiagnostic:
    """A detected agent operational disease or loop condition."""
    pathology_type: PathologyType
    severity: str  # LOW, MEDIUM, CRITICAL
    description: str
    offending_frames: List[str]
    suggested_mitigation: str


class AgentPCAPTracer:
    """
    Captures multi-agent network and execution frames into a timeline and performs
    deterministic root-cause pathology analysis.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or f"pcap-{uuid.uuid4().hex[:10]}"
        self.frames: List[PCAPFrame] = []
        self.start_time = time.time()

    def record_frame(
        self,
        frame_type: FrameType,
        source: str,
        destination: str,
        payload: Dict[str, Any],
        tokens_used: int = 0,
        duration_ms: float = 0.0,
    ) -> PCAPFrame:
        """Capture and append a communication frame."""
        frame = PCAPFrame(
            frame_id=f"f-{len(self.frames) + 1:04d}",
            timestamp=time.time(),
            frame_type=frame_type,
            source=source,
            destination=destination,
            payload=payload,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )
        self.frames.append(frame)
        return frame

    def diagnose_pathologies(self) -> List[PathologyDiagnostic]:
        """
        Perform deterministic, zero-LLM heuristic detection of execution pathologies.
        """
        diagnostics: List[PathologyDiagnostic] = []

        if len(self.frames) < 3:
            return diagnostics

        # 1. Detect Retry Storms (Identical failing tool calls >= 3 times)
        tool_frames = [f for f in self.frames if f.frame_type == FrameType.TOOL]
        if len(tool_frames) >= 3:
            for i in range(len(tool_frames) - 2):
                window = tool_frames[i : i + 3]
                hashes = [f.payload_hash for f in window]
                if len(set(hashes)) == 1:
                    # Check if error is present in payload
                    is_error = any(
                        w.payload.get("success") is False or "error" in w.payload
                        for w in window
                    )
                    if is_error:
                        diagnostics.append(
                            PathologyDiagnostic(
                                pathology_type=PathologyType.RETRY_STORM,
                                severity="CRITICAL",
                                description=f"Detected repetitive retry storm: tool '{window[0].payload.get('tool_name')}' invoked 3 consecutive times with identical failing payload.",
                                offending_frames=[f.frame_id for f in window],
                                suggested_mitigation="Trigger Self-Healing Reflection or trip Circuit Breaker immediately.",
                            )
                        )
                        break

        # 2. Detect Ping-Pong Loops (Agent A <-> Agent B alternating with no state evolution)
        a2a_frames = [f for f in self.frames if f.frame_type == FrameType.A2A]
        if len(a2a_frames) >= 4:
            for i in range(len(a2a_frames) - 3):
                w = a2a_frames[i : i + 4]
                # Check alternating sources: A -> B -> A -> B
                if (
                    w[0].source == w[2].source
                    and w[1].source == w[3].source
                    and w[0].source == w[1].destination
                ):
                    # Check if payloads are essentially static
                    lengths = [len(str(f.payload)) for f in w]
                    if max(lengths) - min(lengths) < 20:
                        diagnostics.append(
                            PathologyDiagnostic(
                                pathology_type=PathologyType.PING_PONG_LOOP,
                                severity="CRITICAL",
                                description=f"Detected Ping-Pong deadlock loop between '{w[0].source}' and '{w[1].source}'.",
                                offending_frames=[f.frame_id for f in w],
                                suggested_mitigation="Force supervisor arbitration or terminate conversation round.",
                            )
                        )
                        break

        # 3. Detect Token Burning Spike (> 12,000 tokens with short output)
        total_tokens = sum(f.tokens_used for f in self.frames)
        total_output_chars = sum(len(str(f.payload.get("output", ""))) for f in self.frames)
        if total_tokens > 12000 and total_output_chars < 500:
            diagnostics.append(
                PathologyDiagnostic(
                    pathology_type=PathologyType.TOKEN_BURNING,
                    severity="HIGH",
                    description=f"Token Burning Anomaly: {total_tokens} tokens consumed but generated only {total_output_chars} characters of output.",
                    offending_frames=[f.frame_id for f in self.frames[-5:]],
                    suggested_mitigation="Switch to Speculative Model Cascade or enable token velocity limits.",
                )
            )

        return diagnostics

    def export_apcap(self) -> Dict[str, Any]:
        """Export session as .apcap bundle."""
        diagnostics = self.diagnose_pathologies()
        return {
            "pcap_version": "1.0.0",
            "session_id": self.session_id,
            "captured_frames": len(self.frames),
            "start_time": self.start_time,
            "end_time": time.time(),
            "total_tokens": sum(f.tokens_used for f in self.frames),
            "diagnostics": [
                {
                    "type": d.pathology_type.value,
                    "severity": d.severity,
                    "description": d.description,
                    "frames": d.offending_frames,
                    "mitigation": d.suggested_mitigation,
                }
                for d in diagnostics
            ],
            "frames": [
                {
                    "id": f.frame_id,
                    "ts": f.timestamp,
                    "type": f.frame_type.value,
                    "src": f.source,
                    "dst": f.destination,
                    "hash": f.payload_hash,
                    "tokens": f.tokens_used,
                    "latency_ms": f.duration_ms,
                    "payload": f.payload,
                }
                for f in self.frames
            ],
        }
