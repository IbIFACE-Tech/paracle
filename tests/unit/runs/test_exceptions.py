"""Tests for paracle_runs exceptions."""


from paracle_runs.exceptions import (
    InvalidRunMetadataError,
    ReplayError,
    RunCleanupError,
    RunLoadError,
    RunNotFoundError,
    RunQueryError,
    RunSaveError,
    RunStorageError,
)


class TestRunStorageError:
    """Test base RunStorageError exception."""

    def test_base_error_creation(self):
        """Test creating base RunStorageError."""
        error = RunStorageError("Storage failed")
        assert str(error) == "Storage failed"
        assert error.error_code == "PARACLE-RUNS-000"
        assert error.message == "Storage failed"

    def test_base_error_is_exception(self):
        """Test RunStorageError is an Exception."""
        error = RunStorageError("Test")
        assert isinstance(error, Exception)


class TestRunNotFoundError:
    """Test RunNotFoundError exception."""

    def test_basic_not_found(self):
        """Test basic run not found error."""
        error = RunNotFoundError("run_123")
        assert "run_123" in str(error)
        assert error.error_code == "PARACLE-RUNS-001"
        assert error.run_id == "run_123"
        assert error.run_type is None

    def test_not_found_with_type(self):
        """Test run not found with run type."""
        error = RunNotFoundError("run_123", run_type="agent")
        assert "run_123" in str(error)
        assert "agent" in str(error).lower()
        assert error.run_type == "agent"

    def test_workflow_not_found(self):
        """Test workflow run not found."""
        error = RunNotFoundError("wf_456", run_type="workflow")
        assert "wf_456" in str(error)
        assert "workflow" in str(error).lower()


class TestReplayError:
    """Test ReplayError exception."""

    def test_replay_error(self):
        """Test replay error with reason."""
        error = ReplayError("run_123", "Missing input data")
        assert "run_123" in str(error)
        assert "Missing input data" in str(error)
        assert error.error_code == "PARACLE-RUNS-002"
        assert error.run_id == "run_123"
        assert error.reason == "Missing input data"

    def test_replay_error_different_reasons(self):
        """Test replay error with various reasons."""
        reasons = [
            "Corrupted metadata",
            "Incompatible version",
            "Missing artifacts",
        ]
        for reason in reasons:
            error = ReplayError("run_abc", reason)
            assert reason in str(error)
            assert error.reason == reason


class TestRunSaveError:
    """Test RunSaveError exception."""

    def test_basic_save_error(self):
        """Test basic save error."""
        error = RunSaveError("run_123", "Disk full")
        assert "run_123" in str(error)
        assert "Disk full" in str(error)
        assert error.error_code == "PARACLE-RUNS-003"
        assert error.run_id == "run_123"
        assert error.reason == "Disk full"
        assert error.original_error is None

    def test_save_error_with_cause(self):
        """Test save error with original exception."""
        original = OSError("Permission denied")
        error = RunSaveError("run_123", "Failed to write",
                             original_error=original)
        assert error.original_error is original
        assert error.__cause__ is original

    def test_save_error_exception_chaining(self):
        """Test proper exception chaining."""
        original = ValueError("Invalid data")
        error = RunSaveError("run_456", "Validation failed",
                             original_error=original)
        assert isinstance(error.__cause__, ValueError)
        assert error.__cause__.args[0] == "Invalid data"


class TestRunLoadError:
    """Test RunLoadError exception."""

    def test_basic_load_error(self):
        """Test basic load error."""
        error = RunLoadError("run_789", "File not found")
        assert "run_789" in str(error)
        assert "File not found" in str(error)
        assert error.error_code == "PARACLE-RUNS-004"
        assert error.run_id == "run_789"
        assert error.reason == "File not found"

    def test_load_error_with_original(self):
        """Test load error with original exception."""
        original = FileNotFoundError("metadata.yaml")
        error = RunLoadError("run_789", "Missing file",
                             original_error=original)
        assert error.__cause__ is original

    def test_load_error_yaml_corruption(self):
        """Test load error for corrupted YAML."""
        error = RunLoadError("run_abc", "Invalid YAML syntax")
        assert "Invalid YAML" in str(error)


class TestRunQueryError:
    """Test RunQueryError exception."""

    def test_basic_query_error(self):
        """Test basic query error."""
        error = RunQueryError("Invalid filter")
        assert "Invalid filter" in str(error)
        assert error.error_code == "PARACLE-RUNS-005"
        assert error.reason == "Invalid filter"
        assert error.query_details is None

    def test_query_error_with_details(self):
        """Test query error with query details."""
        error = RunQueryError(
            "Invalid date range",
            query_details="since=2026-01-01, until=2025-12-31",
        )
        assert "Invalid date range" in str(error)
        assert "since=2026-01-01" in str(error)
        assert error.query_details == "since=2026-01-01, until=2025-12-31"


class TestRunCleanupError:
    """Test RunCleanupError exception."""

    def test_basic_cleanup_error(self):
        """Test basic cleanup error."""
        error = RunCleanupError("Cleanup failed")
        assert "Cleanup failed" in str(error)
        assert error.error_code == "PARACLE-RUNS-006"
        assert error.reason == "Cleanup failed"
        assert error.run_id is None
        assert error.failed_count is None

    def test_cleanup_error_with_run_id(self):
        """Test cleanup error for specific run."""
        error = RunCleanupError("Permission denied", run_id="run_123")
        assert "run_123" in str(error)
        assert error.run_id == "run_123"

    def test_cleanup_error_with_count(self):
        """Test cleanup error with failed count."""
        error = RunCleanupError("Partial failure", failed_count=5)
        assert "5" in str(error)
        assert error.failed_count == 5


class TestInvalidRunMetadataError:
    """Test InvalidRunMetadataError exception."""

    def test_basic_metadata_error(self):
        """Test basic metadata validation error."""
        error = InvalidRunMetadataError("Missing required field")
        assert "Missing required field" in str(error)
        assert error.error_code == "PARACLE-RUNS-007"
        assert error.reason == "Missing required field"
        assert error.field is None

    def test_metadata_error_with_field(self):
        """Test metadata error with field name."""
        error = InvalidRunMetadataError("Must be positive", field="duration")
        assert "duration" in str(error)
        assert "Must be positive" in str(error)
        assert error.field == "duration"

    def test_metadata_error_various_fields(self):
        """Test metadata errors for different fields."""
        fields = ["status", "cost_total_usd", "tokens_total"]
        for field in fields:
            error = InvalidRunMetadataError("Invalid value", field=field)
            assert field in str(error)


class TestExceptionHierarchy:
    """Test exception inheritance and hierarchy."""

    def test_all_inherit_from_storage_error(self):
        """Test all exceptions inherit from RunStorageError."""
        exceptions = [
            RunNotFoundError("run_1"),
            ReplayError("run_2", "reason"),
            RunSaveError("run_3", "reason"),
            RunLoadError("run_4", "reason"),
            RunQueryError("reason"),
            RunCleanupError("reason"),
            InvalidRunMetadataError("reason"),
        ]
        for exc in exceptions:
            assert isinstance(exc, RunStorageError)
            assert isinstance(exc, Exception)

    def test_error_code_uniqueness(self):
        """Test that all error codes are unique."""
        error_codes = {
            RunStorageError("").error_code,
            RunNotFoundError("id").error_code,
            ReplayError("id", "r").error_code,
            RunSaveError("id", "r").error_code,
            RunLoadError("id", "r").error_code,
            RunQueryError("r").error_code,
            RunCleanupError("r").error_code,
            InvalidRunMetadataError("r").error_code,
        }
        assert len(error_codes) == 8  # All unique

    def test_error_codes_follow_convention(self):
        """Test error codes follow PARACLE-RUNS-XXX convention."""
        exceptions = [
            RunStorageError(""),
            RunNotFoundError("id"),
            ReplayError("id", "r"),
            RunSaveError("id", "r"),
            RunLoadError("id", "r"),
            RunQueryError("r"),
            RunCleanupError("r"),
            InvalidRunMetadataError("r"),
        ]
        for exc in exceptions:
            assert exc.error_code.startswith("PARACLE-RUNS-")
            parts = exc.error_code.split("-")
            assert len(parts) == 3
            assert parts[2].isdigit()

    def test_all_have_message_attribute(self):
        """Test all exceptions have message attribute."""
        error = RunNotFoundError("run_123")
        assert hasattr(error, "message")
        assert error.message in str(error)
