"""
SLA monitoring and tracking for Agent Factory Platform.

Tracks service level objectives (SLOs) and service level indicators (SLIs).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class SLIType(str, Enum):
    """Service Level Indicator types."""

    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class SLI:
    """Service Level Indicator."""

    id: str
    name: str
    sli_type: SLIType
    target: float  # Target value (e.g., 0.99 for 99%)
    window_minutes: int = 60  # Measurement window
    measurement_func: Callable | None = None


@dataclass
class SLO:
    """Service Level Objective."""

    id: str
    name: str
    description: str
    slis: list[SLI]
    target_percent: float = 99.9  # Target compliance percentage
    window_days: int = 30  # Compliance window


@dataclass
class SLIMeasurement:
    """SLI measurement."""

    sli_id: str
    timestamp: datetime
    value: float
    metadata: dict = field(default_factory=dict)


class SLAMonitor:
    """
    Monitors SLAs, SLOs, and SLIs.

    Example:
        >>> monitor = SLAMonitor()
        >>> sli = monitor.create_sli("api_availability", SLIType.AVAILABILITY, target=0.99)
        >>> monitor.record_measurement("api_availability", value=0.995)
        >>> status = monitor.get_sli_status("api_availability")
    """

    def __init__(self):
        """Initialize SLA monitor."""
        self.slis: dict[str, SLI] = {}
        self.slos: dict[str, SLO] = {}
        self.measurements: dict[str, list[SLIMeasurement]] = {}

    def create_sli(
        self,
        name: str,
        sli_type: SLIType,
        target: float,
        window_minutes: int = 60,
        measurement_func: Callable | None = None,
    ) -> SLI:
        """
        Create a Service Level Indicator.

        Args:
            name: SLI name
            sli_type: SLI type
            target: Target value
            window_minutes: Measurement window
            measurement_func: Optional measurement function

        Returns:
            Created SLI
        """
        import uuid

        sli_id = str(uuid.uuid4())

        sli = SLI(
            id=sli_id,
            name=name,
            sli_type=sli_type,
            target=target,
            window_minutes=window_minutes,
            measurement_func=measurement_func,
        )

        self.slis[sli_id] = sli
        self.measurements[sli_id] = []

        return sli

    def create_slo(
        self,
        name: str,
        description: str,
        sli_ids: list[str],
        target_percent: float = 99.9,
        window_days: int = 30,
    ) -> SLO:
        """
        Create a Service Level Objective.

        Args:
            name: SLO name
            description: SLO description
            sli_ids: List of SLI IDs
            target_percent: Target compliance percentage
            window_days: Compliance window in days

        Returns:
            Created SLO
        """
        import uuid

        slo_id = str(uuid.uuid4())

        slis = [self.slis[sli_id] for sli_id in sli_ids if sli_id in self.slis]

        slo = SLO(
            id=slo_id,
            name=name,
            description=description,
            slis=slis,
            target_percent=target_percent,
            window_days=window_days,
        )

        self.slos[slo_id] = slo
        return slo

    def record_measurement(
        self,
        sli_id: str,
        value: float,
        metadata: dict | None = None,
    ) -> None:
        """
        Record an SLI measurement.

        Args:
            sli_id: SLI ID
            value: Measurement value
            metadata: Optional metadata
        """
        if sli_id not in self.slis:
            raise ValueError(f"SLI not found: {sli_id}")

        measurement = SLIMeasurement(
            sli_id=sli_id,
            timestamp=datetime.utcnow(),
            value=value,
            metadata=metadata or {},
        )

        self.measurements[sli_id].append(measurement)

        # Keep only recent measurements (last 7 days)
        cutoff = datetime.utcnow() - timedelta(days=7)
        self.measurements[sli_id] = [m for m in self.measurements[sli_id] if m.timestamp > cutoff]

    def get_sli_status(self, sli_id: str) -> dict[str, any]:
        """
        Get SLI status.

        Args:
            sli_id: SLI ID

        Returns:
            Status dictionary
        """
        sli = self.slis.get(sli_id)
        if not sli:
            raise ValueError(f"SLI not found: {sli_id}")

        measurements = self.measurements.get(sli_id, [])

        if not measurements:
            return {
                "sli_id": sli_id,
                "sli_name": sli.name,
                "target": sli.target,
                "current_value": None,
                "is_meeting_target": None,
                "measurement_count": 0,
            }

        # Calculate current value based on window
        window_start = datetime.utcnow() - timedelta(minutes=sli.window_minutes)
        recent_measurements = [m for m in measurements if m.timestamp > window_start]

        if not recent_measurements:
            return {
                "sli_id": sli_id,
                "sli_name": sli.name,
                "target": sli.target,
                "current_value": None,
                "is_meeting_target": None,
                "measurement_count": 0,
            }

        # Calculate value based on SLI type
        if sli.sli_type == SLIType.AVAILABILITY:
            # Availability: percentage of successful requests
            successful = sum(1 for m in recent_measurements if m.value > 0)
            current_value = successful / len(recent_measurements) if recent_measurements else 0.0
        elif sli.sli_type == SLIType.LATENCY:
            # Latency: average latency
            current_value = sum(m.value for m in recent_measurements) / len(recent_measurements)
        elif sli.sli_type == SLIType.ERROR_RATE:
            # Error rate: percentage of errors
            errors = sum(1 for m in recent_measurements if m.value > 0)
            current_value = errors / len(recent_measurements) if recent_measurements else 0.0
        elif sli.sli_type == SLIType.THROUGHPUT:
            # Throughput: requests per second
            time_span = (
                recent_measurements[-1].timestamp - recent_measurements[0].timestamp
            ).total_seconds()
            current_value = len(recent_measurements) / time_span if time_span > 0 else 0.0
        else:
            current_value = sum(m.value for m in recent_measurements) / len(recent_measurements)

        is_meeting_target = self._check_target(sli.sli_type, current_value, sli.target)

        return {
            "sli_id": sli_id,
            "sli_name": sli.name,
            "sli_type": sli.sli_type.value,
            "target": sli.target,
            "current_value": current_value,
            "is_meeting_target": is_meeting_target,
            "measurement_count": len(recent_measurements),
            "window_minutes": sli.window_minutes,
        }

    def _check_target(self, sli_type: SLIType, current_value: float, target: float) -> bool:
        """Check if current value meets target."""
        if sli_type == SLIType.LATENCY:
            # For latency, lower is better
            return current_value <= target
        elif sli_type == SLIType.ERROR_RATE:
            # For error rate, lower is better
            return current_value <= target
        else:
            # For availability and throughput, higher is better
            return current_value >= target

    def get_slo_status(self, slo_id: str) -> dict[str, any]:
        """
        Get SLO status.

        Args:
            slo_id: SLO ID

        Returns:
            Status dictionary
        """
        slo = self.slos.get(slo_id)
        if not slo:
            raise ValueError(f"SLO not found: {slo_id}")

        # Get status for each SLI
        sli_statuses = []

        for sli in slo.slis:
            status = self.get_sli_status(sli.id)
            sli_statuses.append(status)
            if not status.get("is_meeting_target", False):
                pass

        # Calculate compliance percentage
        window_start = datetime.utcnow() - timedelta(days=slo.window_days)
        total_measurements = 0
        meeting_target = 0

        for sli in slo.slis:
            measurements = [
                m for m in self.measurements.get(sli.id, []) if m.timestamp > window_start
            ]
            total_measurements += len(measurements)

            for measurement in measurements:
                if self._check_target(sli.sli_type, measurement.value, sli.target):
                    meeting_target += 1

        compliance_percent = (
            (meeting_target / total_measurements * 100) if total_measurements > 0 else 100.0
        )

        is_meeting_slo = compliance_percent >= slo.target_percent

        return {
            "slo_id": slo_id,
            "slo_name": slo.name,
            "target_percent": slo.target_percent,
            "compliance_percent": compliance_percent,
            "is_meeting_slo": is_meeting_slo,
            "sli_statuses": sli_statuses,
            "window_days": slo.window_days,
        }


# Global instance
_sla_monitor: SLAMonitor | None = None


def get_sla_monitor() -> SLAMonitor:
    """Get global SLA monitor instance."""
    global _sla_monitor
    if _sla_monitor is None:
        _sla_monitor = SLAMonitor()
    return _sla_monitor
