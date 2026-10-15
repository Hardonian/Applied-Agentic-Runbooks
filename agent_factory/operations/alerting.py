"""
Alerting system for Agent Factory Platform.

Supports multiple alert channels and alert rules.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertChannel(str, Enum):
    """Alert channels."""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class AlertRule:
    """Alert rule definition."""
    id: str
    name: str
    condition: Callable[[dict[str, Any]], bool]
    severity: AlertSeverity
    channels: list[AlertChannel]
    enabled: bool = True
    cooldown_seconds: int = 300  # Prevent spam
    last_triggered: datetime | None = None


@dataclass
class Alert:
    """Alert instance."""
    id: str
    rule_id: str
    severity: AlertSeverity
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False


class AlertManager:
    """
    Manages alerts and alerting rules.
    
    Example:
        >>> manager = AlertManager()
        >>> rule = manager.create_rule(
        ...     name="High Error Rate",
        ...     condition=lambda metrics: metrics.get("error_rate", 0) > 0.05,
        ...     severity=AlertSeverity.HIGH,
        ...     channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
        ... )
        >>> manager.check_alerts({"error_rate": 0.1})
    """
    
    def __init__(self):
        """Initialize alert manager."""
        self.rules: dict[str, AlertRule] = {}
        self.alerts: list[Alert] = []
        self.logger = logging.getLogger(__name__)
    
    def create_rule(
        self,
        name: str,
        condition: Callable[[dict[str, Any]], bool],
        severity: AlertSeverity,
        channels: list[AlertChannel],
        cooldown_seconds: int = 300,
    ) -> AlertRule:
        """
        Create an alert rule.
        
        Args:
            name: Rule name
            condition: Condition function that takes metrics dict
            severity: Alert severity
            channels: List of alert channels
            cooldown_seconds: Cooldown period between alerts
            
        Returns:
            Created rule
        """
        import uuid
        rule_id = str(uuid.uuid4())
        
        rule = AlertRule(
            id=rule_id,
            name=name,
            condition=condition,
            severity=severity,
            channels=channels,
            cooldown_seconds=cooldown_seconds,
        )
        
        self.rules[rule_id] = rule
        return rule
    
    def check_alerts(self, metrics: dict[str, Any]) -> list[Alert]:
        """
        Check metrics against alert rules and trigger alerts.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule.last_triggered:
                elapsed = (datetime.utcnow() - rule.last_triggered).total_seconds()
                if elapsed < rule.cooldown_seconds:
                    continue
            
            # Check condition
            try:
                if rule.condition(metrics):
                    alert = self._trigger_alert(rule, metrics)
                    triggered_alerts.append(alert)
                    rule.last_triggered = datetime.utcnow()
            except Exception as e:
                self.logger.error(f"Error evaluating alert rule {rule.id}: {e}")
        
        return triggered_alerts
    
    def _trigger_alert(self, rule: AlertRule, metrics: dict[str, Any]) -> Alert:
        """Trigger an alert."""
        import uuid
        alert_id = str(uuid.uuid4())
        
        message = f"Alert: {rule.name} triggered"
        
        alert = Alert(
            id=alert_id,
            rule_id=rule.id,
            severity=rule.severity,
            message=message,
            metadata=metrics,
        )
        
        self.alerts.append(alert)
        
        # Send to channels
        for channel in rule.channels:
            self._send_alert(channel, alert)
        
        return alert
    
    def _send_alert(self, channel: AlertChannel, alert: Alert) -> None:
        """Send alert to a channel."""
        if channel == AlertChannel.LOG:
            level = {
                AlertSeverity.CRITICAL: logging.CRITICAL,
                AlertSeverity.HIGH: logging.ERROR,
                AlertSeverity.MEDIUM: logging.WARNING,
                AlertSeverity.LOW: logging.WARNING,
                AlertSeverity.INFO: logging.INFO,
            }.get(alert.severity, logging.WARNING)
            
            self.logger.log(level, alert.message, extra=alert.metadata)
        
        elif channel == AlertChannel.EMAIL:
            # Would integrate with email service
            self.logger.info(f"Email alert: {alert.message}")
        
        elif channel == AlertChannel.SLACK:
            # Would integrate with Slack API
            self.logger.info(f"Slack alert: {alert.message}")
        
        elif channel == AlertChannel.PAGERDUTY:
            # Would integrate with PagerDuty API
            self.logger.info(f"PagerDuty alert: {alert.message}")
        
        elif channel == AlertChannel.WEBHOOK:
            # Would send HTTP POST to webhook URL
            self.logger.info(f"Webhook alert: {alert.message}")
    
    def acknowledge_alert(self, alert_id: str) -> None:
        """Acknowledge an alert."""
        alert = next((a for a in self.alerts if a.id == alert_id), None)
        if alert:
            alert.acknowledged = True
    
    def resolve_alert(self, alert_id: str) -> None:
        """Resolve an alert."""
        alert = next((a for a in self.alerts if a.id == alert_id), None)
        if alert:
            alert.resolved = True
    
    def get_active_alerts(
        self,
        severity: AlertSeverity | None = None,
    ) -> list[Alert]:
        """
        Get active (unresolved) alerts.
        
        Args:
            severity: Filter by severity
            
        Returns:
            List of active alerts
        """
        alerts = [a for a in self.alerts if not a.resolved]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def setup_default_rules(self) -> None:
        """Setup default alert rules."""
        # High error rate
        self.create_rule(
            name="High Error Rate",
            condition=lambda m: m.get("error_rate", 0) > 0.05,
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
        )
        
        # High latency
        self.create_rule(
            name="High Latency",
            condition=lambda m: m.get("p95_latency", 0) > 5000,  # 5 seconds
            severity=AlertSeverity.MEDIUM,
            channels=[AlertChannel.EMAIL],
        )
        
        # Low availability
        self.create_rule(
            name="Low Availability",
            condition=lambda m: m.get("availability", 1.0) < 0.99,
            severity=AlertSeverity.CRITICAL,
            channels=[AlertChannel.EMAIL, AlertChannel.PAGERDUTY],
        )
        
        # Budget exceeded
        self.create_rule(
            name="Budget Exceeded",
            condition=lambda m: m.get("budget_exceeded", False),
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
        )


# Global instance
_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    """Get global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
        _alert_manager.setup_default_rules()
    return _alert_manager
