"""Paracle Production Observability Package.

Provides production-grade monitoring and observability:
- Prometheus metrics export
- OpenTelemetry distributed tracing
- Grafana dashboard integration
- Intelligent alerting system
- Jaeger trace visualization
- Centralized error registry and analytics
- Error dashboard and automated reporting

Phase 7 - Production Observability deliverables.
Phase 8 - Error Management Enhancement.
"""

from paracle_observability.alerting import (
    Alert,
    AlertManager,
    AlertRule,
    AlertSeverity,
    NotificationChannel,
    get_alert_manager,
)
from paracle_observability.error_dashboard import ErrorDashboard
from paracle_observability.error_registry import (
    ErrorRecord,
    ErrorRegistry,
    get_error_registry,
)
from paracle_observability.error_registry import ErrorSeverity as ErrorSeverityLevel
from paracle_observability.error_reporter import AutomatedErrorReporter
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
from paracle_observability.metrics import (
    MetricsExporter,
    PrometheusRegistry,
    get_metrics_registry,
    metric_counter,
    metric_gauge,
    metric_histogram,
)
from paracle_observability.tracing import (
    TracingProvider,
    get_tracer,
    trace_async,
    trace_span,
)

__version__ = "1.3.0"

__all__ = [
    # Exceptions
    "ObservabilityError",
    "MetricsError",
    "TracingError",
    "AlertingError",
    "MetricRegistrationError",
    "SpanContextError",
    "AlertRuleError",
    "AlertChannelError",
    "ExporterError",
    # Metrics
    "MetricsExporter",
    "PrometheusRegistry",
    "get_metrics_registry",
    "metric_counter",
    "metric_gauge",
    "metric_histogram",
    # Tracing
    "TracingProvider",
    "get_tracer",
    "trace_span",
    "trace_async",
    # Error Registry (Phase 8)
    "ErrorRegistry",
    "ErrorRecord",
    "ErrorSeverityLevel",
    "get_error_registry",
    # Error Dashboard & Reporting (Phase 8)
    "ErrorDashboard",
    "AutomatedErrorReporter",
    # Alerting
    "Alert",
    "AlertRule",
    "AlertSeverity",
    "AlertManager",
    "NotificationChannel",
    "get_alert_manager",
]
