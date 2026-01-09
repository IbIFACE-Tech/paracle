"""Tests for error registry."""

import json
import time

import pytest
from paracle_observability.error_registry import (
    ErrorRecord,
    ErrorRegistry,
    ErrorSeverity,
    get_error_registry,
)


class TestErrorRecordCreation:
    """Test error record creation."""

    def test_create_error_record(self):
        """Test creating an error record."""
        error_record = ErrorRecord(
            id="test-001",
            timestamp=time.time(),
            error_type="ValueError",
            error_code="PARACLE-TEST-001",
            message="Test error",
            component="test_component",
        )

        assert error_record.id == "test-001"
        assert error_record.error_type == "ValueError"
        assert error_record.error_code == "PARACLE-TEST-001"
        assert error_record.message == "Test error"
        assert error_record.component == "test_component"
        assert error_record.severity == ErrorSeverity.ERROR
        assert error_record.count == 1
        assert error_record.first_seen is not None
        assert error_record.last_seen is not None

    def test_error_record_to_dict(self):
        """Test converting error record to dictionary."""
        error_record = ErrorRecord(
            id="test-001",
            timestamp=123.456,
            error_type="ValueError",
            error_code=None,
            message="Test error",
            component="test_component",
            context={"key": "value"},
        )

        data = error_record.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "test-001"
        assert data["error_type"] == "ValueError"
        assert data["message"] == "Test error"
        assert data["context"] == {"key": "value"}


class TestErrorRegistryBasics:
    """Test error registry basic functionality."""

    def test_create_registry(self):
        """Test creating error registry."""
        registry = ErrorRegistry()

        assert len(registry.errors) == 0
        assert len(registry.error_counts) == 0
        assert len(registry.component_errors) == 0

    def test_record_error(self):
        """Test recording an error."""
        registry = ErrorRegistry()
        error = ValueError("Test error")

        record = registry.record_error(
            error=error,
            component="test_component",
            context={"key": "value"},
        )

        assert record.error_type == "ValueError"
        assert record.message == "Test error"
        assert record.component == "test_component"
        assert record.context == {"key": "value"}
        assert len(registry.errors) == 1
        assert registry.error_counts["ValueError"] == 1

    def test_record_error_without_traceback(self):
        """Test recording error without traceback."""
        registry = ErrorRegistry()
        error = ValueError("Test error")

        record = registry.record_error(
            error=error,
            component="test_component",
            include_traceback=False,
        )

        assert record.stack_trace is None

    def test_record_error_with_severity(self):
        """Test recording error with custom severity."""
        registry = ErrorRegistry()
        error = ValueError("Test error")

        record = registry.record_error(
            error=error,
            component="test_component",
            severity=ErrorSeverity.CRITICAL,
        )

        assert record.severity == ErrorSeverity.CRITICAL


class TestErrorDeduplication:
    """Test error deduplication."""

    def test_deduplicate_same_error(self):
        """Test deduplicating identical errors."""
        registry = ErrorRegistry()
        error1 = ValueError("Connection timeout")
        error2 = ValueError("Connection timeout")

        record1 = registry.record_error(error1, "api_client")
        time.sleep(0.01)
        record2 = registry.record_error(error2, "api_client")

        assert record1.id == record2.id
        assert record1.count == 2
        assert len(registry.errors) == 1  # Only one record stored

    def test_different_errors_not_deduplicated(self):
        """Test different errors are not deduplicated."""
        registry = ErrorRegistry()
        error1 = ValueError("Error 1")
        error2 = ValueError("Error 2")

        record1 = registry.record_error(error1, "component1")
        record2 = registry.record_error(error2, "component2")

        assert record1.id != record2.id
        assert len(registry.errors) == 2


class TestErrorRetrieval:
    """Test error retrieval."""

    def test_get_all_errors(self):
        """Test getting all errors."""
        registry = ErrorRegistry()

        for i in range(5):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        errors = registry.get_errors()
        assert len(errors) == 5

    def test_get_errors_with_limit(self):
        """Test getting errors with limit."""
        registry = ErrorRegistry()

        for i in range(10):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        errors = registry.get_errors(limit=5)
        assert len(errors) == 5

    def test_get_errors_since_timestamp(self):
        """Test filtering errors by timestamp."""
        registry = ErrorRegistry()

        # Record old error
        error1 = ValueError("Old error")
        registry.record_error(error1, "test_component")

        # Wait and get timestamp
        time.sleep(0.1)
        since_time = time.time()

        # Record new errors
        for i in range(3):
            error = ValueError(f"New error {i}")
            registry.record_error(error, "test_component")

        errors = registry.get_errors(since=since_time)
        assert len(errors) == 3

    def test_get_errors_by_severity(self):
        """Test filtering errors by severity."""
        registry = ErrorRegistry()

        error1 = ValueError("Warning error")
        registry.record_error(error1, "test", severity=ErrorSeverity.WARNING)

        error2 = ValueError("Critical error")
        registry.record_error(error2, "test", severity=ErrorSeverity.CRITICAL)

        warnings = registry.get_errors(severity=ErrorSeverity.WARNING)
        assert len(warnings) == 1
        assert warnings[0].severity == ErrorSeverity.WARNING

    def test_get_errors_by_component(self):
        """Test filtering errors by component."""
        registry = ErrorRegistry()

        error1 = ValueError("API error")
        registry.record_error(error1, "api_client")

        error2 = ValueError("DB error")
        registry.record_error(error2, "database")

        api_errors = registry.get_errors(component="api_client")
        assert len(api_errors) == 1
        assert api_errors[0].component == "api_client"

    def test_get_errors_by_component_method(self):
        """Test get_errors_by_component method."""
        registry = ErrorRegistry()

        for i in range(3):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        errors = registry.get_errors_by_component("test_component")
        assert len(errors) == 3

    def test_get_errors_by_type(self):
        """Test get_errors_by_type method."""
        registry = ErrorRegistry()

        error1 = ValueError("Value error")
        registry.record_error(error1, "test")

        error2 = TypeError("Type error")
        registry.record_error(error2, "test")

        error3 = ValueError("Another value error")
        registry.record_error(error3, "test")

        value_errors = registry.get_errors_by_type("ValueError")
        assert len(value_errors) == 2


class TestErrorStatistics:
    """Test error statistics."""

    def test_get_error_count(self):
        """Test getting error count."""
        registry = ErrorRegistry()

        for i in range(5):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        count = registry.get_error_count()
        assert count == 5

    def test_get_statistics(self):
        """Test getting statistics."""
        registry = ErrorRegistry()

        # Record some errors
        for i in range(3):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        stats = registry.get_statistics()

        assert stats["total_count"] == 3
        assert stats["unique_errors"] == 3
        assert "uptime_seconds" in stats
        assert "error_rate_per_minute" in stats
        assert "top_error_types" in stats
        assert "top_components" in stats
        assert "severity_breakdown" in stats

    def test_statistics_top_error_types(self):
        """Test statistics include top error types."""
        registry = ErrorRegistry()

        # Record multiple errors of different types
        for i in range(3):
            error = ValueError(f"Value error {i}")
            registry.record_error(error, "test")

        for i in range(2):
            error = TypeError(f"Type error {i}")
            registry.record_error(error, "test")

        stats = registry.get_statistics()
        top_types = stats["top_error_types"]

        assert len(top_types) >= 2
        assert top_types[0]["type"] == "ValueError"
        assert top_types[0]["count"] == 3

    def test_statistics_top_components(self):
        """Test statistics include top components."""
        registry = ErrorRegistry()

        # Record errors in different components
        for i in range(3):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "component_a")

        for i in range(2):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "component_b")

        stats = registry.get_statistics()
        top_components = stats["top_components"]

        assert len(top_components) >= 2
        assert top_components[0]["component"] == "component_a"
        assert top_components[0]["count"] == 3


class TestPatternDetection:
    """Test error pattern detection."""

    def test_high_frequency_pattern(self):
        """Test detecting high frequency errors."""
        registry = ErrorRegistry()

        # Record 15 DIFFERENT errors to avoid deduplication
        for i in range(15):
            error = ValueError(f"High frequency error {i}")
            registry.record_error(error, "test_component")

        patterns = registry.get_patterns()

        # Should detect high frequency pattern
        high_freq = [p for p in patterns if p["pattern_type"] == "high_frequency"]
        assert len(high_freq) >= 1

    def test_cascading_errors_pattern(self):
        """Test detecting cascading errors in component."""
        registry = ErrorRegistry()

        # Record 10 different errors in same component
        for i in range(10):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "failing_component")

        patterns = registry.get_patterns()

        # Should detect cascading pattern
        cascading = [p for p in patterns if p["pattern_type"] == "cascading"]
        assert len(cascading) >= 1
        assert cascading[0]["component"] == "failing_component"


class TestErrorSearch:
    """Test error search functionality."""

    def test_search_by_message(self):
        """Test searching errors by message."""
        registry = ErrorRegistry()

        error1 = ValueError("Connection timeout occurred")
        registry.record_error(error1, "api_client")

        error2 = ValueError("Invalid response format")
        registry.record_error(error2, "parser")

        results = registry.search_errors("timeout", field="message")
        assert len(results) == 1
        assert "timeout" in results[0].message

    def test_search_case_insensitive(self):
        """Test case-insensitive search."""
        registry = ErrorRegistry()

        error = ValueError("CONNECTION Timeout")
        registry.record_error(error, "api_client")

        results = registry.search_errors(
            "connection", field="message", case_sensitive=False
        )
        assert len(results) == 1

    def test_search_by_component(self):
        """Test searching errors by component."""
        registry = ErrorRegistry()

        error1 = ValueError("Error 1")
        registry.record_error(error1, "api_client")

        error2 = ValueError("Error 2")
        registry.record_error(error2, "database")

        results = registry.search_errors("api", field="component")
        assert len(results) == 1
        assert results[0].component == "api_client"


class TestErrorExport:
    """Test error export functionality."""

    def test_export_to_json(self):
        """Test exporting errors to JSON."""
        registry = ErrorRegistry()

        error = ValueError("Test error")
        registry.record_error(error, "test_component", context={"key": "value"})

        exported = registry.export_errors(format="json")

        assert isinstance(exported, str)
        data = json.loads(exported)
        assert "exported_at" in data
        assert data["count"] == 1
        assert len(data["errors"]) == 1

    def test_export_with_limit(self):
        """Test exporting errors with limit."""
        registry = ErrorRegistry()

        for i in range(10):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        exported = registry.export_errors(format="json", limit=5)
        data = json.loads(exported)

        assert data["count"] == 5
        assert len(data["errors"]) == 5

    def test_export_unsupported_format(self):
        """Test exporting with unsupported format raises error."""
        registry = ErrorRegistry()

        with pytest.raises(ValueError, match="Unsupported format"):
            registry.export_errors(format="xml")


class TestErrorRegistryManagement:
    """Test error registry management."""

    def test_max_errors_limit(self):
        """Test max errors limit is enforced."""
        registry = ErrorRegistry(max_errors=10)

        # Record 15 errors
        for i in range(15):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        # Should only store 10 most recent
        assert len(registry.errors) == 10

    def test_clear_registry(self):
        """Test clearing registry."""
        registry = ErrorRegistry()

        for i in range(5):
            error = ValueError(f"Error {i}")
            registry.record_error(error, "test_component")

        registry.clear()

        assert len(registry.errors) == 0
        assert len(registry.error_counts) == 0
        assert len(registry.component_errors) == 0


class TestGlobalRegistry:
    """Test global registry singleton."""

    def test_get_global_registry(self):
        """Test getting global registry."""
        registry1 = get_error_registry()
        registry2 = get_error_registry()

        # Should return same instance
        assert registry1 is registry2

    def test_global_registry_persists_errors(self):
        """Test global registry persists errors across calls."""
        registry = get_error_registry()
        registry.clear()  # Start fresh

        error = ValueError("Test error")
        registry.record_error(error, "test_component")

        # Get registry again
        registry2 = get_error_registry()
        assert len(registry2.errors) >= 1


class TestErrorSeverityDetermination:
    """Test automatic error severity determination."""

    def test_memory_error_is_critical(self):
        """Test MemoryError is marked as critical."""
        registry = ErrorRegistry()
        error = MemoryError("Out of memory")

        record = registry.record_error(error, "test")
        assert record.severity == ErrorSeverity.CRITICAL

    def test_connection_error_is_warning(self):
        """Test connection errors are warnings."""
        registry = ErrorRegistry()

        # Create a custom ConnectionError-like exception
        class ConnectionError(Exception):
            pass

        error = ConnectionError("Connection failed")
        record = registry.record_error(error, "test")

        # ConnectionError in name should be detected as WARNING
        assert record.severity == ErrorSeverity.WARNING

    def test_default_error_severity(self):
        """Test default error severity."""
        registry = ErrorRegistry()
        error = ValueError("Some error")

        record = registry.record_error(error, "test")
        assert record.severity == ErrorSeverity.ERROR
