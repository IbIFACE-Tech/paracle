"""Tests for intelligent alerting."""

import time

from paracle_observability.alerting import (
    Alert,
    AlertManager,
    AlertRule,
    AlertSeverity,
    AlertState,
    EmailChannel,
    SlackChannel,
    WebhookChannel,
    get_alert_manager,
)


def test_alert_creation():
    """Test alert creation."""
    alert = Alert(
        rule_name="high_error_rate",
        severity=AlertSeverity.ERROR,
        message="Error rate above threshold",
        labels={"service": "api", "env": "prod"},
    )

    assert alert.rule_name == "high_error_rate"
    assert alert.severity == AlertSeverity.ERROR
    assert alert.state == AlertState.PENDING
    assert alert.fingerprint != ""


def test_alert_state_transitions():
    """Test alert state transitions."""
    alert = Alert(
        rule_name="test",
        severity=AlertSeverity.WARNING,
        message="Test alert",
    )

    assert alert.state == AlertState.PENDING

    alert.fire()
    assert alert.state == AlertState.FIRING

    alert.resolve()
    assert alert.state == AlertState.RESOLVED
    assert alert.ends_at is not None

    alert.silence()
    assert alert.state == AlertState.SILENCED


def test_alert_rule_evaluation():
    """Test alert rule evaluation."""
    error_count = 0

    def condition():
        return error_count > 10

    rule = AlertRule(
        name="high_error_count",
        severity=AlertSeverity.ERROR,
        condition=condition,
        message="Error count above 10",
        for_duration=1.0,  # 1 second
    )

    # Condition not met
    alert = rule.evaluate()
    assert alert is None

    # Condition met but not for duration
    error_count = 15
    alert = rule.evaluate()
    assert alert is None

    # Condition met for duration
    time.sleep(1.1)
    alert = rule.evaluate()
    assert alert is not None
    assert alert.severity == AlertSeverity.ERROR
    assert alert.state == AlertState.FIRING


def test_alert_rule_error_handling():
    """Test alert rule error handling."""

    def failing_condition():
        raise ValueError("Condition evaluation failed")

    rule = AlertRule(
        name="failing_rule",
        severity=AlertSeverity.WARNING,
        condition=failing_condition,
        message="Test",
    )

    alert = rule.evaluate()
    assert alert is not None
    assert alert.severity == AlertSeverity.ERROR
    assert "evaluation_error" in alert.labels.get("error", "")


def test_slack_channel():
    """Test Slack notification channel."""
    channel = SlackChannel(
        "slack",
        {"webhook_url": "https://hooks.slack.com/test"},
    )

    alert = Alert(
        rule_name="test",
        severity=AlertSeverity.WARNING,
        message="Test alert",
        labels={"env": "test"},
    )

    result = channel.send(alert)
    assert result is True


def test_email_channel():
    """Test email notification channel."""
    channel = EmailChannel(
        "email",
        {"to": "ops@example.com", "from": "alerts@example.com"},
    )

    alert = Alert(
        rule_name="test",
        severity=AlertSeverity.ERROR,
        message="Test alert",
    )

    result = channel.send(alert)
    assert result is True


def test_webhook_channel():
    """Test webhook notification channel."""
    channel = WebhookChannel(
        "webhook",
        {"url": "https://example.com/webhook"},
    )

    alert = Alert(
        rule_name="test",
        severity=AlertSeverity.CRITICAL,
        message="Test alert",
    )

    result = channel.send(alert)
    assert result is True


def test_alert_manager():
    """Test alert manager."""
    manager = AlertManager()

    # Add rule
    counter = 0

    def condition():
        return counter > 5

    rule = AlertRule(
        name="test_rule",
        severity=AlertSeverity.WARNING,
        condition=condition,
        message="Counter above 5",
        for_duration=0.1,  # 0.1 seconds
    )

    manager.add_rule(rule)

    # Add channel
    channel = WebhookChannel("test", {"url": "https://example.com"})
    manager.add_channel(channel)

    # Evaluate - condition not met
    alerts = manager.evaluate_rules()
    assert len(alerts) == 0

    # Evaluate - condition met
    counter = 10
    alerts = manager.evaluate_rules()  # Start timing
    assert len(alerts) == 0  # Not yet - duration not met

    time.sleep(0.15)  # Wait for duration
    alerts = manager.evaluate_rules()  # Check again
    assert len(alerts) == 1  # Now it fires

    # Check active alerts
    active = manager.get_active_alerts()
    assert len(active) == 1
    assert active[0].rule_name == "test_rule"


def test_alert_manager_silence():
    """Test alert silencing."""
    manager = AlertManager()

    counter = 10

    def condition():
        return counter > 5

    rule = AlertRule(
        name="test_rule",
        severity=AlertSeverity.WARNING,
        condition=condition,
        message="Counter above 5",
        for_duration=0.1,
    )

    manager.add_rule(rule)

    # Create alert
    manager.evaluate_rules()  # Start timing
    time.sleep(0.15)
    alerts = manager.evaluate_rules()  # Fire alert
    assert len(alerts) == 1

    # Silence alert
    fingerprint = alerts[0].fingerprint
    manager.silence(fingerprint, duration=1.0)

    # Evaluate again - should be silenced
    alerts = manager.evaluate_rules()
    active = manager.get_active_alerts()
    assert active[0].state == AlertState.SILENCED


def test_alert_manager_by_severity():
    """Test filtering alerts by severity."""
    manager = AlertManager()

    # Add multiple rules with different severities
    def always_true():
        return True

    for severity in [
        AlertSeverity.INFO,
        AlertSeverity.WARNING,
        AlertSeverity.ERROR,
    ]:
        rule = AlertRule(
            name=f"rule_{severity.value}",
            severity=severity,
            condition=always_true,
            message=f"Test {severity.value}",
            for_duration=0.1,
        )
        manager.add_rule(rule)

    manager.evaluate_rules()  # Start timing
    time.sleep(0.15)
    manager.evaluate_rules()  # Fire alerts

    # Get all active alerts
    all_alerts = manager.get_active_alerts()
    assert len(all_alerts) == 3

    # Get only ERROR alerts
    error_alerts = manager.get_active_alerts(AlertSeverity.ERROR)
    assert len(error_alerts) == 1
    assert error_alerts[0].severity == AlertSeverity.ERROR


def test_global_alert_manager():
    """Test global alert manager instance."""
    manager1 = get_alert_manager()
    manager2 = get_alert_manager()

    assert manager1 is manager2
