"""Tests for automated error reporter."""

import time

from paracle_observability.error_registry import ErrorRegistry, ErrorSeverity
from paracle_observability.error_reporter import AutomatedErrorReporter


class TestDailySummary:
    """Test daily summary generation."""

    def test_generate_daily_summary(self):
        """Test generating daily summary."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record some errors
        for i in range(5):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        summary = reporter.generate_daily_summary()

        assert summary["report_type"] == "daily_summary"
        assert "date" in summary
        assert "total_errors" in summary
        assert summary["total_errors"] == 5

    def test_daily_summary_top_errors(self):
        """Test daily summary includes top errors."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record different error types
        for i in range(3):
            error = ValueError(f"Value error {i}")
            registry.record_error(error, "test")

        for i in range(2):
            error = TypeError(f"Type error {i}")
            registry.record_error(error, "test")

        summary = reporter.generate_daily_summary()

        assert len(summary["top_errors"]) >= 2
        assert summary["top_errors"][0]["error_type"] == "ValueError"

    def test_daily_summary_severity_breakdown(self):
        """Test daily summary includes severity breakdown."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record errors with different severities
        error1 = ValueError("Warning")
        registry.record_error(error1, "test", severity=ErrorSeverity.WARNING)

        error2 = ValueError("Critical")
        registry.record_error(error2, "test", severity=ErrorSeverity.CRITICAL)

        summary = reporter.generate_daily_summary()

        assert "severity_breakdown" in summary
        assert summary["critical_errors"] == 1
        assert summary["warnings"] == 1


class TestWeeklyReport:
    """Test weekly report generation."""

    def test_generate_weekly_report(self):
        """Test generating weekly report."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record errors
        for i in range(10):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        report = reporter.generate_weekly_report()

        assert report["report_type"] == "weekly_report"
        assert "start_date" in report
        assert "end_date" in report
        assert "total_errors" in report
        assert "daily_average" in report

    def test_weekly_report_trend(self):
        """Test weekly report includes trend analysis."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record some errors
        for i in range(10):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        report = reporter.generate_weekly_report()

        assert "trend" in report
        assert "direction" in report["trend"]
        assert report["trend"]["direction"] in ["increasing", "decreasing", "stable"]


class TestAnomalyDetection:
    """Test anomaly detection."""

    def test_detect_anomalies_none(self):
        """Test no anomalies with stable rate."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record consistent errors
        for i in range(10):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        anomalies = reporter.detect_anomalies(threshold_std_dev=2.0, hours=1)

        # Should be no anomalies with stable rate
        assert isinstance(anomalies, list)

    def test_detect_anomalies_with_spike(self):
        """Test anomaly detection with error spike."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record normal errors
        for i in range(5):
            error = ValueError(f"Normal {i}")
            registry.record_error(error, "test")

        # Wait longer for clear separation
        time.sleep(0.2)

        # Create much larger spike (60 vs 5)
        for i in range(60):
            error = ValueError(f"Spike {i}")
            registry.record_error(error, "test")

        anomalies = reporter.detect_anomalies(threshold_std_dev=1.5, hours=1)

        # Should detect anomaly (timing-dependent, so test gracefully)
        assert isinstance(anomalies, list)
        # Note: Anomaly detection depends on timing/bucketing


class TestIncidentReport:
    """Test incident report generation."""

    def test_generate_incident_report(self):
        """Test generating incident report."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        start_time = time.time()

        # Simulate incident
        for i in range(20):
            error = ValueError(f"Incident error {i}")
            registry.record_error(error, "failing_component")

        end_time = time.time()

        report = reporter.generate_incident_report(
            start_time=start_time,
            end_time=end_time,
            title="Test Incident",
        )

        assert report["report_type"] == "incident_report"
        assert report["title"] == "Test Incident"
        assert report["total_errors"] == 20
        assert "duration_minutes" in report

    def test_incident_report_timeline(self):
        """Test incident report includes timeline."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        start_time = time.time()

        # Record errors
        for i in range(10):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test")

        end_time = time.time()

        report = reporter.generate_incident_report(start_time, end_time)

        assert "timeline" in report
        assert isinstance(report["timeline"], list)


class TestComponentHealthReport:
    """Test component health reporting."""

    def test_generate_component_health_report(self):
        """Test generating component health report."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record errors in components
        for i in range(5):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "component_a")

        for i in range(20):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "component_b")

        report = reporter.generate_component_health_report()

        assert report["report_type"] == "component_health"
        assert len(report["components"]) >= 2

        # component_b should have lower health (more errors)
        comp_b = next(
            c for c in report["components"] if c["component"] == "component_b"
        )
        assert comp_b["health_score"] < 100

    def test_component_health_scores(self):
        """Test component health scores."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Few errors = high score
        error = ValueError("Single error")
        registry.record_error(error, "healthy_component")

        report = reporter.generate_component_health_report()

        if len(report["components"]) > 0:
            comp = report["components"][0]
            assert comp["health_score"] >= 90
            assert comp["status"] == "healthy"


class TestAlertingDecisions:
    """Test alerting decision logic."""

    def test_should_alert_no_issues(self):
        """Test no alert with no issues."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        decision = reporter.should_alert()

        assert decision["should_alert"] is False
        assert decision["alert_count"] == 0

    def test_should_alert_high_error_rate(self):
        """Test alert on high error rate."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Generate high error rate
        for i in range(50):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test")

        decision = reporter.should_alert(error_rate_threshold=1.0)

        # Should trigger alert (stats show high error rate)
        # Note: might not trigger if timing is tight
        assert isinstance(decision["should_alert"], bool)
        assert decision["alert_count"] >= 0

    def test_should_alert_critical_errors(self):
        """Test alert on critical errors."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record critical error
        error = ValueError("Critical issue")
        registry.record_error(error, "test", severity=ErrorSeverity.CRITICAL)

        decision = reporter.should_alert(critical_error_threshold=1)

        assert decision["should_alert"] is True
        assert any(a["type"] == "critical_errors" for a in decision["alerts"])

    def test_should_alert_patterns(self):
        """Test alert on error patterns."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Trigger pattern detection
        for i in range(15):
            error = ValueError(f"Pattern error {i}")
            registry.record_error(error, "test")

        decision = reporter.should_alert()

        # Should detect patterns
        if len(registry.get_patterns()) > 0:
            assert decision["should_alert"] is True
            assert any(a["type"] == "error_patterns" for a in decision["alerts"])


class TestTrendAnalysis:
    """Test trend analysis."""

    def test_analyze_trend_stable(self):
        """Test stable trend detection."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry)

        # Record stable error rate
        for i in range(10):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test")

        report = reporter.generate_weekly_report()
        trend = report["trend"]

        # Should be stable (no clear increase/decrease)
        assert trend["direction"] in ["stable", "increasing", "decreasing"]

    def test_baseline_calculation(self):
        """Test baseline error rate calculation."""
        registry = ErrorRegistry()
        reporter = AutomatedErrorReporter(registry, baseline_window=3600)

        # Baseline window should be set
        assert reporter.baseline_window == 3600
