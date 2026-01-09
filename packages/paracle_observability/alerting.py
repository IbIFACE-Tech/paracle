"""Intelligent alerting system for Paracle.

Provides rule-based alerting with multiple notification channels:
- Alert rules with thresholds and conditions
- Notification channels (Slack, Email, PagerDuty, Webhook)
- Alert aggregation and deduplication
- Silence rules
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertState(str, Enum):
    """Alert states."""

    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class Alert:
    """Alert instance."""

    rule_name: str
    severity: AlertSeverity
    message: str
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    state: AlertState = AlertState.PENDING
    starts_at: float = field(default_factory=time.time)
    ends_at: float | None = None
    fingerprint: str = ""

    def __post_init__(self):
        """Generate fingerprint."""
        if not self.fingerprint:
            label_str = "_".join(f"{k}={v}" for k, v in sorted(self.labels.items()))
            self.fingerprint = f"{self.rule_name}_{label_str}"

    def fire(self):
        """Mark alert as firing."""
        self.state = AlertState.FIRING

    def resolve(self):
        """Mark alert as resolved."""
        self.state = AlertState.RESOLVED
        self.ends_at = time.time()

    def silence(self):
        """Silence alert."""
        self.state = AlertState.SILENCED

    @property
    def duration_seconds(self) -> float:
        """Get alert duration."""
        end = self.ends_at or time.time()
        return end - self.starts_at


class AlertRule:
    """Alert rule definition."""

    def __init__(
        self,
        name: str,
        severity: AlertSeverity,
        condition: Callable[[], bool],
        message: str,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        for_duration: float = 60.0,  # seconds
    ):
        self.name = name
        self.severity = severity
        self.condition = condition
        self.message = message
        self.labels = labels or {}
        self.annotations = annotations or {}
        self.for_duration = for_duration
        self._condition_true_since: float | None = None
        self._last_check: float | None = None

    def evaluate(self) -> Alert | None:
        """Evaluate rule and return alert if firing."""
        now = time.time()
        self._last_check = now

        try:
            condition_met = self.condition()
        except Exception as e:
            # Rule evaluation error
            return Alert(
                rule_name=self.name,
                severity=AlertSeverity.ERROR,
                message=f"Rule evaluation error: {e}",
                labels={"rule": self.name, "error": "evaluation_error"},
            )

        if condition_met:
            # Condition is true
            if self._condition_true_since is None:
                self._condition_true_since = now

            # Check if condition has been true for required duration
            duration = now - self._condition_true_since
            if duration >= self.for_duration:
                alert = Alert(
                    rule_name=self.name,
                    severity=self.severity,
                    message=self.message,
                    labels=self.labels.copy(),
                    annotations=self.annotations.copy(),
                )
                alert.fire()
                return alert
        else:
            # Condition is false
            self._condition_true_since = None

        return None


class NotificationChannel:
    """Base notification channel."""

    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config

    def send(self, alert: Alert) -> bool:
        """Send alert notification."""
        raise NotImplementedError


class SlackChannel(NotificationChannel):
    """Slack notification channel."""

    def send(self, alert: Alert) -> bool:
        """Send to Slack."""
        # Implementation would use Slack API
        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            return False

        payload = {
            "text": f"🚨 {alert.severity.value.upper()}: {alert.message}",
            "attachments": [
                {
                    "color": self._severity_color(alert.severity),
                    "fields": [
                        {"title": k, "value": v, "short": True}
                        for k, v in alert.labels.items()
                    ],
                }
            ],
        }

        # Would send HTTP POST to webhook_url
        print(f"[Slack] {alert.message}")
        return True

    def _severity_color(self, severity: AlertSeverity) -> str:
        """Get color for severity."""
        colors = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "danger",
            AlertSeverity.CRITICAL: "danger",
        }
        return colors.get(severity, "warning")


class EmailChannel(NotificationChannel):
    """Email notification channel."""

    def send(self, alert: Alert) -> bool:
        """Send email."""
        to_address = self.config.get("to")
        if not to_address:
            return False

        subject = f"[{alert.severity.value.upper()}] {alert.rule_name}"
        body = f"""
Alert: {alert.rule_name}
Severity: {alert.severity.value}
Message: {alert.message}
State: {alert.state.value}
Started: {time.ctime(alert.starts_at)}

Labels:
{chr(10).join(f"  {k}: {v}" for k, v in alert.labels.items())}

Annotations:
{chr(10).join(f"  {k}: {v}" for k, v in alert.annotations.items())}
        """

        # Would send email via SMTP
        print(f"[Email] To: {to_address}, Subject: {subject}")
        return True


class WebhookChannel(NotificationChannel):
    """Generic webhook notification channel."""

    def send(self, alert: Alert) -> bool:
        """Send to webhook."""
        url = self.config.get("url")
        if not url:
            return False

        payload = {
            "rule_name": alert.rule_name,
            "severity": alert.severity.value,
            "message": alert.message,
            "state": alert.state.value,
            "labels": alert.labels,
            "annotations": alert.annotations,
            "starts_at": alert.starts_at,
            "ends_at": alert.ends_at,
        }

        # Would send HTTP POST
        print(f"[Webhook] {url}: {alert.message}")
        return True


class AlertManager:
    """Manages alerts and notifications."""

    def __init__(self):
        self._rules: dict[str, AlertRule] = {}
        self._channels: dict[str, NotificationChannel] = {}
        self._active_alerts: dict[str, Alert] = {}
        self._alert_history: list[Alert] = []
        self._silences: dict[str, float] = {}  # fingerprint -> until timestamp

    def add_rule(self, rule: AlertRule):
        """Add alert rule."""
        self._rules[rule.name] = rule

    def add_channel(self, channel: NotificationChannel):
        """Add notification channel."""
        self._channels[channel.name] = channel

    def silence(self, fingerprint: str, duration: float = 3600.0):
        """Silence alert for duration (seconds)."""
        self._silences[fingerprint] = time.time() + duration

    def evaluate_rules(self) -> list[Alert]:
        """Evaluate all rules and return new alerts."""
        new_alerts = []

        for rule in self._rules.values():
            alert = rule.evaluate()
            if alert:
                fingerprint = alert.fingerprint

                # Check if silenced
                if fingerprint in self._silences:
                    if time.time() < self._silences[fingerprint]:
                        alert.silence()
                    else:
                        # Silence expired
                        del self._silences[fingerprint]

                # Check if this is a new alert
                if fingerprint not in self._active_alerts:
                    self._active_alerts[fingerprint] = alert
                    new_alerts.append(alert)
                    self._notify(alert)
                else:
                    # Update existing alert
                    self._active_alerts[fingerprint] = alert

        # Check for resolved alerts
        self._check_resolved_alerts()

        return new_alerts

    def _check_resolved_alerts(self):
        """Check for alerts that should be resolved."""
        to_resolve = []

        for fingerprint, alert in self._active_alerts.items():
            # Check if rule still exists and condition is still true
            rule = self._rules.get(alert.rule_name)
            if rule is None:
                # Rule was removed
                to_resolve.append(fingerprint)
            else:
                try:
                    # Check if condition is no longer met
                    if not rule.condition():
                        to_resolve.append(fingerprint)
                except Exception:
                    # Error evaluating - keep alert active
                    pass

        for fingerprint in to_resolve:
            alert = self._active_alerts[fingerprint]
            alert.resolve()
            self._alert_history.append(alert)
            del self._active_alerts[fingerprint]
            self._notify(alert)

    def _notify(self, alert: Alert):
        """Send notifications for alert."""
        if alert.state == AlertState.SILENCED:
            return

        for channel in self._channels.values():
            try:
                channel.send(alert)
            except Exception as e:
                print(f"[AlertManager] Failed to send to {channel.name}: {e}")

    def get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]:
        """Get active alerts."""
        alerts = list(self._active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts

    def get_alert_history(self, limit: int = 100) -> list[Alert]:
        """Get alert history."""
        return self._alert_history[-limit:]


# Global alert manager
_global_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    """Get global alert manager."""
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
    return _global_alert_manager
