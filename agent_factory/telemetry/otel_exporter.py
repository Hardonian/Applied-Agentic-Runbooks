"""Dependency-free OpenTelemetry bridge for AgentPCAP and VeriDAG evidence."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from agent_factory.orchestration.veridag import VeriDAGExecutionProof
from agent_factory.telemetry.pcap import PCAPFrame


@dataclass
class OTelExportResult:
    """Observable outcome of an export attempt."""

    exported: bool
    signal: str
    item_count: int
    reason: str = ""


@dataclass
class OTelExporter:
    """Translate native evidence into OTLP JSON and Prometheus text formats.

    When no endpoint is configured, conversion remains available and exporting is a
    deliberate no-op. This preserves fully offline execution with no OTel SDK install.
    """

    endpoint: str | None = None
    service_name: str = "agent-factory"
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        self.endpoint = self.endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        configured_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
        for item in configured_headers.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                self.headers.setdefault(key.strip(), value.strip())

    @property
    def enabled(self) -> bool:
        """Whether remote export is configured."""
        return bool(self.endpoint)

    def frames_to_otlp(self, frames: list[PCAPFrame | dict[str, Any]]) -> dict[str, Any]:
        """Represent AgentPCAP frames as standard OTLP log records."""
        records = []
        for frame in frames:
            if isinstance(frame, PCAPFrame):
                signal_name = frame.frame_type.value
                if signal_name == "tool":
                    signal_name = "tool_call"
                elif signal_name == "model":
                    signal_name = "model_call"
                payload = {
                    "frame_id": frame.frame_id,
                    "frame_type": signal_name,
                    "source": frame.source,
                    "destination": frame.destination,
                    "payload_hash": frame.payload_hash,
                    "tokens_used": frame.tokens_used,
                    "duration_ms": frame.duration_ms,
                    "payload": frame.payload,
                }
                timestamp = frame.timestamp
            else:
                payload = dict(frame)
                timestamp = float(payload.get("ts", payload.get("timestamp", time.time())))
            records.append(
                {
                    "timeUnixNano": str(int(timestamp * 1_000_000_000)),
                    "severityText": "INFO",
                    "body": {"stringValue": str(payload.get("frame_type", "agentpcap"))},
                    "attributes": [
                        {"key": "agent.factory.signal", "value": {"stringValue": "agentpcap"}},
                        {
                            "key": "agent.factory.payload",
                            "value": {
                                "stringValue": json.dumps(payload, sort_keys=True, default=str)
                            },
                        },
                    ],
                }
            )
        return {
            "resourceLogs": [
                {
                    "resource": self._resource(),
                    "scopeLogs": [
                        {"scope": {"name": "agent_factory.telemetry.pcap"}, "logRecords": records}
                    ],
                }
            ]
        }

    def veridag_to_otlp(self, proof: VeriDAGExecutionProof | dict[str, Any]) -> dict[str, Any]:
        """Represent VeriDAG node transitions as OTLP spans for Jaeger/collectors."""
        data = proof.to_dict() if isinstance(proof, VeriDAGExecutionProof) else proof
        execution_id = str(data["execution_id"])
        trace_id = self._hex_id(execution_id, 32)
        spans = []
        for node_id, node in data.get("node_proofs", {}).items():
            duration = float(node.get("execution_time", 0.0))
            end_ns = int(float(data.get("timestamp", time.time())) * 1_000_000_000)
            spans.append(
                {
                    "traceId": trace_id,
                    "spanId": self._hex_id(f"{execution_id}:{node_id}", 16),
                    "name": f"veridag.{node_id}",
                    "kind": 1,
                    "startTimeUnixNano": str(max(0, end_ns - int(duration * 1_000_000_000))),
                    "endTimeUnixNano": str(end_ns),
                    "attributes": [
                        {
                            "key": "veridag.merkle_hash",
                            "value": {"stringValue": str(node.get("state_merkle_hash", ""))},
                        },
                        {
                            "key": "veridag.executor_id",
                            "value": {"stringValue": str(node.get("executor_id", "agent"))},
                        },
                    ],
                    "status": {"code": 1 if data.get("is_valid", True) else 2},
                }
            )
        return {
            "resourceSpans": [
                {
                    "resource": self._resource(),
                    "scopeSpans": [
                        {"scope": {"name": "agent_factory.orchestration.veridag"}, "spans": spans}
                    ],
                }
            ]
        }

    def veridag_to_otlp_spans(
        self, proof: VeriDAGExecutionProof | dict[str, Any]
    ) -> dict[str, Any]:
        """Compatibility trace view containing a root DAG span and child step spans."""
        if isinstance(proof, VeriDAGExecutionProof) and proof.step_order:
            execution_id = proof.execution_id
            end_ns = int(proof.timestamp * 1_000_000_000)
            trace_id = self._hex_id(execution_id, 32)
            root_id = self._hex_id(f"{execution_id}:root", 16)
            spans: list[dict[str, Any]] = [
                {
                    "traceId": trace_id,
                    "spanId": root_id,
                    "name": f"veridag.{proof.dag_id or proof.workflow_name or 'execution'}",
                    "startTimeUnixNano": str(end_ns),
                    "endTimeUnixNano": str(end_ns),
                    "attributes": [],
                    "status": {"code": 1 if proof.is_valid else 2},
                }
            ]
            for step_id in proof.step_order:
                spans.append(
                    {
                        "traceId": trace_id,
                        "spanId": self._hex_id(f"{execution_id}:{step_id}", 16),
                        "parentSpanId": root_id,
                        "name": f"veridag.{step_id}",
                        "startTimeUnixNano": str(end_ns),
                        "endTimeUnixNano": str(end_ns),
                        "attributes": [
                            {
                                "key": "veridag.step_hash",
                                "value": {"stringValue": proof.step_hashes.get(step_id, "")},
                            }
                        ],
                        "status": {"code": 1},
                    }
                )
            return {
                "resourceSpans": [
                    {
                        "resource": self._resource(),
                        "scopeSpans": [
                            {
                                "scope": {"name": "agent_factory.orchestration.veridag"},
                                "spans": spans,
                            }
                        ],
                    }
                ]
            }
        return self.veridag_to_otlp(proof)

    @staticmethod
    def metrics_to_prometheus(metrics: dict[str, float], prefix: str = "agent_factory") -> str:
        """Convert a numeric metric mapping to Prometheus exposition format."""
        lines: list[str] = []
        for name, value in sorted(metrics.items()):
            safe_name = "".join(char if char.isalnum() or char == "_" else "_" for char in name)
            lines.append(f"{prefix}_{safe_name} {value}")
        return "\n".join(lines) + "\n"

    def prometheus_metrics(
        self,
        frames: list[PCAPFrame | dict[str, Any]],
        proof: VeriDAGExecutionProof | dict[str, Any] | None = None,
    ) -> str:
        """Render low-cardinality Prometheus exposition text."""
        token_total = 0
        latency_total = 0.0
        for frame in frames:
            if isinstance(frame, PCAPFrame):
                token_total += frame.tokens_used
                latency_total += frame.duration_ms
            else:
                token_total += int(frame.get("tokens", frame.get("tokens_used", 0)))
                latency_total += float(frame.get("latency_ms", frame.get("duration_ms", 0.0)))
        valid = 1
        if proof is not None:
            valid = int(
                proof.is_valid
                if isinstance(proof, VeriDAGExecutionProof)
                else proof.get("is_valid", True)
            )
        return "\n".join(
            [
                "# HELP agent_factory_pcap_frames_total Captured AgentPCAP frames.",
                "# TYPE agent_factory_pcap_frames_total counter",
                f"agent_factory_pcap_frames_total {len(frames)}",
                "# HELP agent_factory_tokens_total Tokens observed in captured frames.",
                "# TYPE agent_factory_tokens_total counter",
                f"agent_factory_tokens_total {token_total}",
                "# HELP agent_factory_frame_latency_ms_total Aggregate frame latency.",
                "# TYPE agent_factory_frame_latency_ms_total counter",
                f"agent_factory_frame_latency_ms_total {latency_total}",
                "# HELP agent_factory_veridag_valid Last VeriDAG proof validity.",
                "# TYPE agent_factory_veridag_valid gauge",
                f"agent_factory_veridag_valid {valid}",
                "",
            ]
        )

    def export_frames(self, frames: list[PCAPFrame | dict[str, Any]]) -> OTelExportResult:
        """Export AgentPCAP frames through OTLP/HTTP JSON when configured."""
        return self._export("logs", self.frames_to_otlp(frames), len(frames))

    def export_veridag(self, proof: VeriDAGExecutionProof | dict[str, Any]) -> OTelExportResult:
        """Export VeriDAG spans through OTLP/HTTP JSON when configured."""
        payload = self.veridag_to_otlp(proof)
        count = len(payload["resourceSpans"][0]["scopeSpans"][0]["spans"])
        return self._export("traces", payload, count)

    def _export(self, signal: str, payload: dict[str, Any], count: int) -> OTelExportResult:
        if not self.endpoint:
            return OTelExportResult(False, signal, count, "OTLP endpoint is not configured")
        url = f"{self.endpoint.rstrip('/')}/v1/{signal}"
        # B310: urllib.request.urlopen will happily open file://, ftp:// and
        # other schemes, so a misconfigured endpoint would read local files
        # instead of exporting telemetry. Restrict to real OTLP transports.
        scheme = urllib.parse.urlparse(url).scheme
        if scheme not in ("http", "https"):
            return OTelExportResult(
                False,
                signal,
                count,
                f"Rejected non-HTTP OTLP endpoint scheme: {scheme or '(none)'}",
            )
        headers = {"Content-Type": "application/json", **self.headers}
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )
        try:
            # nosec B310 -- scheme already restricted to http/https above;
            # bandit cannot see the guard that precedes this call.
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310
                exported = 200 <= response.status < 300
                return OTelExportResult(exported, signal, count, f"HTTP {response.status}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return OTelExportResult(False, signal, count, str(exc))

    def _resource(self) -> dict[str, Any]:
        return {
            "attributes": [
                {
                    "key": "service.name",
                    "value": {"stringValue": self.service_name},
                }
            ]
        }

    @staticmethod
    def _hex_id(value: str, length: int) -> str:
        import hashlib

        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


OpenTelemetryBridge = OTelExporter
