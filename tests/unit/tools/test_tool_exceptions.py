"""Tests for paracle_tools exceptions."""


from paracle_tools.exceptions import (
    ToolConfigurationError,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolPermissionError,
    ToolRegistrationError,
    ToolResourceError,
    ToolTimeoutError,
    ToolValidationError,
)


class TestToolError:
    """Test base ToolError exception."""

    def test_base_error_creation(self):
        """Test creating base ToolError."""
        error = ToolError("Tool failed")
        assert str(error) == "Tool failed"
        assert error.error_code == "PARACLE-TOOL-000"
        assert error.message == "Tool failed"

    def test_base_error_is_exception(self):
        """Test ToolError is an Exception."""
        error = ToolError("Test")
        assert isinstance(error, Exception)


class TestToolExecutionError:
    """Test ToolExecutionError exception."""

    def test_basic_execution_error(self):
        """Test basic tool execution error."""
        error = ToolExecutionError("git_commit", "Command failed")
        assert "git_commit" in str(error)
        assert "Command failed" in str(error)
        assert error.error_code == "PARACLE-TOOL-001"
        assert error.tool_name == "git_commit"
        assert error.reason == "Command failed"
        assert error.original_error is None

    def test_execution_error_with_original(self):
        """Test execution error with original exception."""
        original = RuntimeError("Process crashed")
        error = ToolExecutionError(
            "shell_exec",
            "Execution failed",
            original_error=original,
        )
        assert error.original_error is original
        assert error.__cause__ is original
        assert isinstance(error.__cause__, RuntimeError)


class TestToolValidationError:
    """Test ToolValidationError exception."""

    def test_basic_validation_error(self):
        """Test basic tool validation error."""
        error = ToolValidationError("file_writer", "Missing parameter")
        assert "file_writer" in str(error)
        assert "Missing parameter" in str(error)
        assert error.error_code == "PARACLE-TOOL-002"
        assert error.tool_name == "file_writer"
        assert error.reason == "Missing parameter"
        assert error.field is None

    def test_validation_error_with_field(self):
        """Test validation error with field name."""
        error = ToolValidationError(
            "api_call",
            "Invalid format",
            field="url",
        )
        assert "url" in str(error)
        assert error.field == "url"


class TestToolNotFoundError:
    """Test ToolNotFoundError exception."""

    def test_not_found_error(self):
        """Test tool not found error."""
        error = ToolNotFoundError("custom_analyzer")
        assert "custom_analyzer" in str(error)
        assert error.error_code == "PARACLE-TOOL-003"
        assert error.tool_name == "custom_analyzer"


class TestToolTimeoutError:
    """Test ToolTimeoutError exception."""

    def test_timeout_error(self):
        """Test tool timeout error."""
        error = ToolTimeoutError("long_running_task", 30.0)
        assert "long_running_task" in str(error)
        assert "30" in str(error)
        assert error.error_code == "PARACLE-TOOL-004"
        assert error.tool_name == "long_running_task"
        assert error.timeout_seconds == 30.0

    def test_timeout_error_different_values(self):
        """Test timeout error with different timeout values."""
        timeouts = [5.0, 60.0, 120.5]
        for timeout in timeouts:
            error = ToolTimeoutError("tool", timeout)
            assert str(timeout) in str(error)
            assert error.timeout_seconds == timeout


class TestToolPermissionError:
    """Test ToolPermissionError exception."""

    def test_basic_permission_error(self):
        """Test basic tool permission error."""
        error = ToolPermissionError("file_deleter", "/etc/passwd")
        assert "file_deleter" in str(error)
        assert "/etc/passwd" in str(error)
        assert error.error_code == "PARACLE-TOOL-005"
        assert error.tool_name == "file_deleter"
        assert error.resource == "/etc/passwd"
        assert error.required_permission is None

    def test_permission_error_with_required_permission(self):
        """Test permission error with required permission."""
        error = ToolPermissionError(
            "database_writer",
            "production_db",
            required_permission="write",
        )
        assert "write" in str(error)
        assert error.required_permission == "write"


class TestToolResourceError:
    """Test ToolResourceError exception."""

    def test_resource_error(self):
        """Test tool resource error."""
        error = ToolResourceError("video_encoder", "memory", "Out of memory")
        assert "video_encoder" in str(error)
        assert "memory" in str(error)
        assert "Out of memory" in str(error)
        assert error.error_code == "PARACLE-TOOL-006"
        assert error.tool_name == "video_encoder"
        assert error.resource_type == "memory"
        assert error.reason == "Out of memory"

    def test_resource_error_different_types(self):
        """Test resource error with different resource types."""
        resource_types = ["cpu", "disk", "network"]
        for rtype in resource_types:
            error = ToolResourceError("tool", rtype, "Limit exceeded")
            assert rtype in str(error)
            assert error.resource_type == rtype


class TestToolRegistrationError:
    """Test ToolRegistrationError exception."""

    def test_registration_error(self):
        """Test tool registration error."""
        error = ToolRegistrationError("duplicate_tool", "Already registered")
        assert "duplicate_tool" in str(error)
        assert "Already registered" in str(error)
        assert error.error_code == "PARACLE-TOOL-007"
        assert error.tool_name == "duplicate_tool"
        assert error.reason == "Already registered"


class TestToolConfigurationError:
    """Test ToolConfigurationError exception."""

    def test_basic_config_error(self):
        """Test basic tool configuration error."""
        error = ToolConfigurationError("api_client", "Missing API key")
        assert "api_client" in str(error)
        assert "Missing API key" in str(error)
        assert error.error_code == "PARACLE-TOOL-008"
        assert error.tool_name == "api_client"
        assert error.reason == "Missing API key"
        assert error.config_key is None

    def test_config_error_with_key(self):
        """Test configuration error with config key."""
        error = ToolConfigurationError(
            "database_tool",
            "Invalid value",
            config_key="connection_timeout",
        )
        assert "connection_timeout" in str(error)
        assert error.config_key == "connection_timeout"


class TestExceptionHierarchy:
    """Test exception inheritance and hierarchy."""

    def test_all_inherit_from_tool_error(self):
        """Test all exceptions inherit from ToolError."""
        exceptions = [
            ToolExecutionError("t", "r"),
            ToolValidationError("t", "r"),
            ToolNotFoundError("t"),
            ToolTimeoutError("t", 30.0),
            ToolPermissionError("t", "res"),
            ToolResourceError("t", "rtype", "r"),
            ToolRegistrationError("t", "r"),
            ToolConfigurationError("t", "r"),
        ]
        for exc in exceptions:
            assert isinstance(exc, ToolError)
            assert isinstance(exc, Exception)

    def test_error_code_uniqueness(self):
        """Test all error codes are unique."""
        error_codes = {
            ToolError("").error_code,
            ToolExecutionError("t", "r").error_code,
            ToolValidationError("t", "r").error_code,
            ToolNotFoundError("t").error_code,
            ToolTimeoutError("t", 1.0).error_code,
            ToolPermissionError("t", "r").error_code,
            ToolResourceError("t", "rt", "r").error_code,
            ToolRegistrationError("t", "r").error_code,
            ToolConfigurationError("t", "r").error_code,
        }
        assert len(error_codes) == 9  # All unique

    def test_error_codes_follow_convention(self):
        """Test error codes follow PARACLE-TOOL-XXX convention."""
        exceptions = [
            ToolError(""),
            ToolExecutionError("t", "r"),
            ToolValidationError("t", "r"),
            ToolNotFoundError("t"),
            ToolTimeoutError("t", 1.0),
            ToolPermissionError("t", "r"),
            ToolResourceError("t", "rt", "r"),
            ToolRegistrationError("t", "r"),
            ToolConfigurationError("t", "r"),
        ]
        for exc in exceptions:
            assert exc.error_code.startswith("PARACLE-TOOL-")
            parts = exc.error_code.split("-")
            assert len(parts) == 3
            assert parts[2].isdigit()

    def test_exception_chaining_works(self):
        """Test exception chaining with __cause__."""
        original = ValueError("Original error")
        error = ToolExecutionError("tool", "Failed", original_error=original)
        assert error.__cause__ is original
        assert isinstance(error.__cause__, ValueError)

    def test_all_have_message_attribute(self):
        """Test all exceptions have message attribute."""
        error = ToolExecutionError("tool", "Failed")
        assert hasattr(error, "message")
        assert error.message in str(error)
