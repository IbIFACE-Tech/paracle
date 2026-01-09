"""Tests for paracle_core exceptions."""

from paracle_core.exceptions import (
    ConfigurationError,
    DependencyError,
    InitializationError,
    ParacleError,
    PermissionError,
    ResourceError,
    StateError,
    ValidationError,
    WorkspaceError,
)


class TestParacleError:
    """Test base ParacleError exception."""

    def test_base_error_creation(self):
        """Test creating base ParacleError."""
        error = ParacleError("Test error")
        assert str(error) == "Test error"
        assert error.error_code == "PARACLE-CORE-000"
        assert error.message == "Test error"

    def test_base_error_is_exception(self):
        """Test ParacleError is an Exception."""
        error = ParacleError("Test")
        assert isinstance(error, Exception)


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_basic_config_error(self):
        """Test basic configuration error."""
        error = ConfigurationError("Invalid value")
        assert str(error) == "Invalid value"
        assert error.error_code == "PARACLE-CORE-001"
        assert error.config_key is None

    def test_config_error_with_key(self):
        """Test configuration error with specific key."""
        error = ConfigurationError("Invalid value", config_key="database.host")
        assert "database.host" in str(error)
        assert "Invalid value" in str(error)
        assert error.config_key == "database.host"

    def test_config_error_inheritance(self):
        """Test ConfigurationError inherits from ParacleError."""
        error = ConfigurationError("Test")
        assert isinstance(error, ParacleError)
        assert isinstance(error, Exception)


class TestInitializationError:
    """Test InitializationError exception."""

    def test_basic_init_error(self):
        """Test basic initialization error."""
        error = InitializationError("Failed to start")
        assert str(error) == "Failed to start"
        assert error.error_code == "PARACLE-CORE-002"
        assert error.component is None

    def test_init_error_with_component(self):
        """Test initialization error with component name."""
        error = InitializationError("Failed to start", component="database")
        assert "database" in str(error)
        assert "Failed to start" in str(error)
        assert error.component == "database"


class TestValidationError:
    """Test ValidationError exception."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        error = ValidationError("Invalid format")
        assert str(error) == "Invalid format"
        assert error.error_code == "PARACLE-CORE-003"
        assert error.field is None
        assert error.value is None

    def test_validation_error_with_field(self):
        """Test validation error with field name."""
        error = ValidationError("Must be positive", field="timeout")
        assert "timeout" in str(error)
        assert "Must be positive" in str(error)
        assert error.field == "timeout"

    def test_validation_error_with_field_and_value(self):
        """Test validation error with field and value."""
        error = ValidationError("Too large", field="max_retries", value="100")
        assert error.field == "max_retries"
        assert error.value == "100"


class TestWorkspaceError:
    """Test WorkspaceError exception."""

    def test_basic_workspace_error(self):
        """Test basic workspace error."""
        error = WorkspaceError("Workspace corrupted")
        assert str(error) == "Workspace corrupted"
        assert error.error_code == "PARACLE-CORE-004"
        assert error.path is None

    def test_workspace_error_with_path(self):
        """Test workspace error with path."""
        error = WorkspaceError("Permission denied", path=".parac/config")
        assert ".parac/config" in str(error)
        assert error.path == ".parac/config"


class TestDependencyError:
    """Test DependencyError exception."""

    def test_basic_dependency_error(self):
        """Test basic dependency error."""
        error = DependencyError("Not installed")
        assert str(error) == "Not installed"
        assert error.error_code == "PARACLE-CORE-005"
        assert error.dependency is None
        assert error.required_version is None

    def test_dependency_error_with_name(self):
        """Test dependency error with dependency name."""
        error = DependencyError("Not found", dependency="redis")
        assert "redis" in str(error)
        assert error.dependency == "redis"

    def test_dependency_error_with_version(self):
        """Test dependency error with version requirement."""
        error = DependencyError(
            "Incompatible version",
            dependency="pydantic",
            required_version="2.0.0",
        )
        assert "pydantic" in str(error)
        assert "2.0.0" in str(error)
        assert error.required_version == "2.0.0"


class TestResourceError:
    """Test ResourceError exception."""

    def test_basic_resource_error(self):
        """Test basic resource error."""
        error = ResourceError("Resource unavailable")
        assert str(error) == "Resource unavailable"
        assert error.error_code == "PARACLE-CORE-006"
        assert error.resource_type is None
        assert error.resource_id is None

    def test_resource_error_with_type(self):
        """Test resource error with resource type."""
        error = ResourceError("Not found", resource_type="file")
        assert "file" in str(error)
        assert error.resource_type == "file"

    def test_resource_error_with_type_and_id(self):
        """Test resource error with type and ID."""
        error = ResourceError(
            "Not found",
            resource_type="workflow",
            resource_id="wf_123",
        )
        assert "workflow" in str(error)
        assert "wf_123" in str(error)
        assert error.resource_id == "wf_123"


class TestStateError:
    """Test StateError exception."""

    def test_basic_state_error(self):
        """Test basic state error."""
        error = StateError("Invalid transition")
        assert str(error) == "Invalid transition"
        assert error.error_code == "PARACLE-CORE-007"
        assert error.current_state is None
        assert error.target_state is None

    def test_state_error_with_states(self):
        """Test state error with current and target states."""
        error = StateError(
            "Not allowed",
            current_state="running",
            target_state="stopped",
        )
        assert "running" in str(error)
        assert "stopped" in str(error)
        assert error.current_state == "running"
        assert error.target_state == "stopped"


class TestPermissionError:
    """Test PermissionError exception."""

    def test_basic_permission_error(self):
        """Test basic permission error."""
        error = PermissionError("Access denied")
        assert str(error) == "Access denied"
        assert error.error_code == "PARACLE-CORE-008"
        assert error.resource is None
        assert error.required_permission is None

    def test_permission_error_with_resource(self):
        """Test permission error with resource and permission."""
        error = PermissionError(
            "Access denied",
            resource="/sensitive/file",
            required_permission="read",
        )
        assert "/sensitive/file" in str(error)
        assert "read" in str(error)
        assert error.resource == "/sensitive/file"
        assert error.required_permission == "read"


class TestExceptionChaining:
    """Test exception chaining and context preservation."""

    def test_exception_chaining_with_cause(self):
        """Test that exceptions can be chained with __cause__."""
        original = ValueError("Original error")
        error = ConfigurationError("Config failed")
        error.__cause__ = original

        assert error.__cause__ is original
        assert isinstance(error.__cause__, ValueError)

    def test_error_code_uniqueness(self):
        """Test that all exception error codes are unique."""
        error_codes = {
            ParacleError("").error_code,
            ConfigurationError("").error_code,
            InitializationError("").error_code,
            ValidationError("").error_code,
            WorkspaceError("").error_code,
            DependencyError("").error_code,
            ResourceError("").error_code,
            StateError("").error_code,
            PermissionError("").error_code,
        }
        # All error codes should be unique
        assert len(error_codes) == 9

    def test_all_errors_have_codes(self):
        """Test that all exceptions have error_code attribute."""
        exceptions = [
            ParacleError(""),
            ConfigurationError(""),
            InitializationError(""),
            ValidationError(""),
            WorkspaceError(""),
            DependencyError(""),
            ResourceError(""),
            StateError(""),
            PermissionError(""),
        ]
        for exc in exceptions:
            assert hasattr(exc, "error_code")
            assert exc.error_code.startswith("PARACLE-CORE-")

    def test_error_codes_follow_convention(self):
        """Test that error codes follow PARACLE-CORE-XXX convention."""
        error = ConfigurationError("Test")
        assert error.error_code.startswith("PARACLE-CORE-")
        assert len(error.error_code.split("-")) == 3
        assert error.error_code.split("-")[2].isdigit()
