"""Tests for paracle_observability exceptions."""

from paracle_observability.exceptions import (
    AlertChannelError,
    AlertingError,
    AlertRuleError,
    ExporterError,
    MetricRegistrationError,
    MetricsError,
    ObservabilityError,
    SpanContextError,
    TracingError,
)


class TestObservabilityError:
    """Test base ObservabilityError exception."""

    def test_base_error_creation(self):
        """Test creating base ObservabilityError."""
        error = ObservabilityError("Observability failed")
        assert str(error) == "Observability failed"
        assert error.error_code == "PARACLE-OBS-000"
        assert error.message == "Observability failed"

    def test_base_error_is_exception(self):
        """Test ObservabilityError is an Exception."""
        error = ObservabilityError("Test")
        assert isinstance(error, Exception)


class TestMetricsError:
    """Test MetricsError exception."""

    def test_basic_metrics_error(self):
        """Test basic metrics error."""
        error = MetricsError("Failed to collect metrics")
        assert "Failed to collect metrics" in str(error)
        assert error.error_code == "PARACLE-OBS-001"
        assert error.metric_name is None
        assert error.metric_type is None

    def test_metrics_error_with_name(self):
        """Test metrics error with metric name."""
        error = MetricsError("Registry error", metric_name="request_count")
        assert "request_count" in str(error)
        assert error.metric_name == "request_count"

    def test_metrics_error_with_type(self):
        """Test metrics error with metric type."""
        error = MetricsError("Invalid type", metric_type="counter")
        assert error.metric_type == "counter"


class TestTracingError:
    """Test TracingError exception."""

    def test_basic_tracing_error(self):
        """Test basic tracing error."""
        error = TracingError("Tracing failed")
        assert "Tracing failed" in str(error)
        assert error.error_code == "PARACLE-OBS-002"
        assert error.span_name is None
        assert error.trace_id is None

    def test_tracing_error_with_span(self):
        """Test tracing error with span name."""
        error = TracingError("Span creation failed", span_name="workflow_execute")
        assert "workflow_execute" in str(error)
        assert error.span_name == "workflow_execute"

    def test_tracing_error_with_trace_id(self):
        """Test tracing error with trace ID."""
        error = TracingError("Export failed", trace_id="trace_abc123")
        assert error.trace_id == "trace_abc123"


class TestAlertingError:
    """Test AlertingError exception."""

    def test_basic_alerting_error(self):
        """Test basic alerting error."""
        error = AlertingError("Alert failed")
        assert "Alert failed" in str(error)
        assert error.error_code == "PARACLE-OBS-003"
        assert error.alert_name is None
        assert error.channel is None

    def test_alerting_error_with_alert_name(self):
        """Test alerting error with alert name."""
        error = AlertingError("Evaluation failed", alert_name="high_error_rate")
        assert "high_error_rate" in str(error)
        assert error.alert_name == "high_error_rate"

    def test_alerting_error_with_channel(self):
        """Test alerting error with channel."""
        error = AlertingError(
            "Delivery failed",
            alert_name="cpu_alert",
            channel="slack",
        )
        assert "slack" in str(error)
        assert error.channel == "slack"


class TestMetricRegistrationError:
    """Test MetricRegistrationError exception."""

    def test_registration_error(self):
        """Test metric registration error."""
        error = MetricRegistrationError("requests_total", "Duplicate metric")
        assert "requests_total" in str(error)
        assert "Duplicate metric" in str(error)
        assert error.error_code == "PARACLE-OBS-004"
        assert error.metric_name == "requests_total"
        assert error.reason == "Duplicate metric"

    def test_registration_error_inheritance(self):
        """Test MetricRegistrationError inherits from MetricsError."""
        error = MetricRegistrationError("metric", "reason")
        assert isinstance(error, MetricsError)
        assert isinstance(error, ObservabilityError)


class TestSpanContextError:
    """Test SpanContextError exception."""

    def test_basic_span_context_error(self):
        """Test basic span context error."""
        error = SpanContextError("Context propagation failed")
        assert "Context propagation failed" in str(error)
        assert error.error_code == "PARACLE-OBS-005"
        assert error.reason == "Context propagation failed"
        assert error.trace_id is None

    def test_span_context_error_with_trace_id(self):
        """Test span context error with trace ID."""
        error = SpanContextError("Invalid context", trace_id="trace_xyz")
        assert error.trace_id == "trace_xyz"

    def test_span_context_error_inheritance(self):
        """Test SpanContextError inherits from TracingError."""
        error = SpanContextError("reason")
        assert isinstance(error, TracingError)
        assert isinstance(error, ObservabilityError)


class TestAlertRuleError:
    """Test AlertRuleError exception."""

    def test_basic_alert_rule_error(self):
        """Test basic alert rule error."""
        error = AlertRuleError("cpu_threshold", "Invalid expression")
        assert "cpu_threshold" in str(error)
        assert "Invalid expression" in str(error)
        assert error.error_code == "PARACLE-OBS-006"
        assert error.rule_name == "cpu_threshold"
        assert error.reason == "Invalid expression"
        assert error.expression is None

    def test_alert_rule_error_with_expression(self):
        """Test alert rule error with expression."""
        error = AlertRuleError(
            "memory_alert",
            "Syntax error",
            expression="memory > 90%",
        )
        assert "memory > 90%" in str(error)
        assert error.expression == "memory > 90%"

    def test_alert_rule_error_inheritance(self):
        """Test AlertRuleError inherits from AlertingError."""
        error = AlertRuleError("rule", "reason")
        assert isinstance(error, AlertingError)
        assert isinstance(error, ObservabilityError)


class TestAlertChannelError:
    """Test AlertChannelError exception."""

    def test_basic_channel_error(self):
        """Test basic alert channel error."""
        error = AlertChannelError("slack", "Webhook failed")
        assert "slack" in str(error)
        assert "Webhook failed" in str(error)
        assert error.error_code == "PARACLE-OBS-007"
        assert error.channel == "slack"
        assert error.reason == "Webhook failed"
        assert error.original_error is None

    def test_channel_error_with_original(self):
        """Test alert channel error with original exception."""
        original = ConnectionError("Network timeout")
        error = AlertChannelError("email", "SMTP failed", original_error=original)
        assert error.original_error is original
        assert error.__cause__ is original
        assert isinstance(error.__cause__, ConnectionError)

    def test_channel_error_inheritance(self):
        """Test AlertChannelError inherits from AlertingError."""
        error = AlertChannelError("channel", "reason")
        assert isinstance(error, AlertingError)
        assert isinstance(error, ObservabilityError)


class TestExporterError:
    """Test ExporterError exception."""

    def test_basic_exporter_error(self):
        """Test basic exporter error."""
        error = ExporterError("Prometheus", "Export failed")
        assert "Prometheus" in str(error)
        assert "Export failed" in str(error)
        assert error.error_code == "PARACLE-OBS-008"
        assert error.exporter_type == "Prometheus"
        assert error.reason == "Export failed"
        assert error.original_error is None

    def test_exporter_error_with_original(self):
        """Test exporter error with original exception."""
        original = TimeoutError("Request timeout")
        error = ExporterError("Jaeger", "Timeout", original_error=original)
        assert error.original_error is original
        assert error.__cause__ is original

    def test_exporter_error_inheritance(self):
        """Test ExporterError inherits from ObservabilityError."""
        error = ExporterError("type", "reason")
        assert isinstance(error, ObservabilityError)
        assert isinstance(error, Exception)


class TestExceptionHierarchy:
    """Test exception inheritance and hierarchy."""

    def test_all_inherit_from_observability_error(self):
        """Test all exceptions inherit from ObservabilityError."""
        exceptions = [
            MetricsError("test"),
            TracingError("test"),
            AlertingError("test"),
            MetricRegistrationError("metric", "reason"),
            SpanContextError("reason"),
            AlertRuleError("rule", "reason"),
            AlertChannelError("channel", "reason"),
            ExporterError("type", "reason"),
        ]
        for exc in exceptions:
            assert isinstance(exc, ObservabilityError)
            assert isinstance(exc, Exception)

    def test_specialized_error_inheritance(self):
        """Test specialized errors inherit from correct base."""
        assert isinstance(MetricRegistrationError("m", "r"), MetricsError)
        assert isinstance(SpanContextError("r"), TracingError)
        assert isinstance(AlertRuleError("r", "e"), AlertingError)
        assert isinstance(AlertChannelError("c", "r"), AlertingError)

    def test_error_code_uniqueness(self):
        """Test all error codes are unique."""
        error_codes = {
            ObservabilityError("").error_code,
            MetricsError("").error_code,
            TracingError("").error_code,
            AlertingError("").error_code,
            MetricRegistrationError("m", "r").error_code,
            SpanContextError("r").error_code,
            AlertRuleError("r", "e").error_code,
            AlertChannelError("c", "r").error_code,
            ExporterError("t", "r").error_code,
        }
        assert len(error_codes) == 9  # All unique

    def test_error_codes_follow_convention(self):
        """Test error codes follow PARACLE-OBS-XXX convention."""
        exceptions = [
            ObservabilityError(""),
            MetricsError(""),
            TracingError(""),
            AlertingError(""),
            MetricRegistrationError("m", "r"),
            SpanContextError("r"),
            AlertRuleError("r", "e"),
            AlertChannelError("c", "r"),
            ExporterError("t", "r"),
        ]
        for exc in exceptions:
            assert exc.error_code.startswith("PARACLE-OBS-")
            parts = exc.error_code.split("-")
            assert len(parts) == 3
            assert parts[2].isdigit()

    def test_exception_chaining_preserved(self):
        """Test exception chaining works correctly."""
        original = ValueError("Original")

        channel_error = AlertChannelError("slack", "Failed", original_error=original)
        assert channel_error.__cause__ is original

        exporter_error = ExporterError("Prometheus", "Failed", original_error=original)
        assert exporter_error.__cause__ is original
