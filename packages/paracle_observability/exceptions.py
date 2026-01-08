"""Observability exceptions.

Exception hierarchy for metrics, tracing, and alerting errors.
"""


class ObservabilityError(Exception):
    """Base exception for observability errors.

    Attributes:
        error_code: Unique error code (PARACLE-OBS-XXX)
        message: Human-readable error message
    """

    error_code: str = "PARACLE-OBS-000"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MetricsError(ObservabilityError):
    """Raised when metrics operations fail.

    Examples:
        - Invalid metric name
        - Metric registry error
        - Export failure
    """

    error_code = "PARACLE-OBS-001"

    def __init__(
        self,
        message: str,
        metric_name: str | None = None,
        metric_type: str | None = None,
    ) -> None:
        self.metric_name = metric_name
        self.metric_type = metric_type
        if metric_name:
            message = f"Metrics error for '{metric_name}': {message}"
        super().__init__(message)


class TracingError(ObservabilityError):
    """Raised when tracing operations fail.

    Examples:
        - Span creation failed
        - Invalid trace context
        - Export failure
    """

    error_code = "PARACLE-OBS-002"

    def __init__(
        self,
        message: str,
        span_name: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        self.span_name = span_name
        self.trace_id = trace_id
        if span_name:
            message = f"Tracing error for span '{span_name}': {message}"
        super().__init__(message)


class AlertingError(ObservabilityError):
    """Raised when alerting operations fail.

    Examples:
        - Invalid alert rule
        - Channel configuration error
        - Alert delivery failure
    """

    error_code = "PARACLE-OBS-003"

    def __init__(
        self,
        message: str,
        alert_name: str | None = None,
        channel: str | None = None,
    ) -> None:
        self.alert_name = alert_name
        self.channel = channel
        if alert_name:
            message = f"Alert error for '{alert_name}': {message}"
        if channel:
            message = f"{message} (channel: {channel})"
        super().__init__(message)


class MetricRegistrationError(MetricsError):
    """Raised when metric registration fails.

    Examples:
        - Duplicate metric name
        - Invalid metric type
        - Registry full
    """

    error_code = "PARACLE-OBS-004"

    def __init__(self, metric_name: str, reason: str) -> None:
        self.metric_name = metric_name
        self.reason = reason
        super().__init__(
            f"Failed to register metric '{metric_name}': {reason}",
            metric_name=metric_name,
        )


class SpanContextError(TracingError):
    """Raised when span context operations fail.

    Examples:
        - Invalid trace context propagation
        - Missing parent span
        - Context serialization error
    """

    error_code = "PARACLE-OBS-005"

    def __init__(self, reason: str, trace_id: str | None = None) -> None:
        self.reason = reason
        message = f"Span context error: {reason}"
        super().__init__(message, trace_id=trace_id)


class AlertRuleError(AlertingError):
    """Raised when alert rule operations fail.

    Examples:
        - Invalid rule expression
        - Rule evaluation error
        - Duplicate rule name
    """

    error_code = "PARACLE-OBS-006"

    def __init__(
        self,
        rule_name: str,
        reason: str,
        expression: str | None = None,
    ) -> None:
        self.rule_name = rule_name
        self.reason = reason
        self.expression = expression
        message = f"Alert rule '{rule_name}' error: {reason}"
        if expression:
            message = f"{message} (expression: {expression})"
        super().__init__(message, alert_name=rule_name)


class AlertChannelError(AlertingError):
    """Raised when alert channel operations fail.

    Examples:
        - Channel not configured
        - Delivery failure
        - Rate limit exceeded
    """

    error_code = "PARACLE-OBS-007"

    def __init__(
        self,
        channel: str,
        reason: str,
        original_error: Exception | None = None,
    ) -> None:
        self.channel = channel
        self.reason = reason
        self.original_error = original_error
        super().__init__(
            f"Alert channel '{channel}' error: {reason}",
            channel=channel,
        )
        if original_error:
            self.__cause__ = original_error


class ExporterError(ObservabilityError):
    """Raised when metric/trace export fails.

    Examples:
        - Export endpoint unreachable
        - Invalid export format
        - Export timeout
    """

    error_code = "PARACLE-OBS-008"

    def __init__(
        self,
        exporter_type: str,
        reason: str,
        original_error: Exception | None = None,
    ) -> None:
        self.exporter_type = exporter_type
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"{exporter_type} exporter error: {reason}")
        if original_error:
            self.__cause__ = original_error
