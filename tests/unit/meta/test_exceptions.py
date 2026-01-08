"""Unit tests for paracle_meta.exceptions module."""

import pytest

from paracle_meta.exceptions import (
    ConfigurationError,
    CostLimitExceededError,
    FeedbackRecordingError,
    GenerationError,
    InvalidArtifactTypeError,
    LearningEngineError,
    ParacleMetaError,
    ProviderNotAvailableError,
    ProviderSelectionError,
    QualityBelowThresholdError,
    TemplateNotFoundError,
)


class TestParacleMetaError:
    """Tests for base exception."""

    def test_create_with_message(self):
        """Test creating exception with message."""
        error = ParacleMetaError("Test error message")
        assert str(error) == "[PARACLE-META-000] Test error message"
        assert error.message == "Test error message"

    def test_create_with_details(self):
        """Test creating exception with details."""
        error = ParacleMetaError(
            "Test error", details={"key": "value", "count": 42}
        )
        assert "key" in error.details
        assert error.details["count"] == 42
        assert "Details:" in str(error)


class TestProviderNotAvailableError:
    """Tests for ProviderNotAvailableError."""

    def test_create_with_provider(self):
        """Test creating error with provider name."""
        error = ProviderNotAvailableError("anthropic")
        assert error.error_code == "PARACLE-META-002"
        assert "anthropic" in str(error)
        assert error.details["provider"] == "anthropic"

    def test_create_with_reason(self):
        """Test creating error with reason."""
        error = ProviderNotAvailableError(
            "openai",
            reason="API key not configured",
            available_providers=["anthropic", "ollama"],
        )
        assert "API key not configured" in str(error)
        assert error.details["available_providers"] == ["anthropic", "ollama"]


class TestGenerationError:
    """Tests for GenerationError."""

    def test_create_generation_error(self):
        """Test creating generation error."""
        error = GenerationError(
            artifact_type="agent",
            name="SecurityAuditor",
            reason="LLM request failed",
            provider="anthropic",
        )
        assert error.error_code == "PARACLE-META-003"
        assert "agent" in str(error)
        assert "SecurityAuditor" in str(error)
        assert error.details["reason"] == "LLM request failed"


class TestQualityBelowThresholdError:
    """Tests for QualityBelowThresholdError."""

    def test_create_quality_error(self):
        """Test creating quality threshold error."""
        error = QualityBelowThresholdError(
            artifact_type="workflow",
            name="DeployWorkflow",
            score=5.5,
            threshold=7.0,
        )
        assert error.error_code == "PARACLE-META-004"
        assert "5.5" in str(error)
        assert "7.0" in str(error)
        assert error.details["score"] == 5.5


class TestCostLimitExceededError:
    """Tests for CostLimitExceededError."""

    def test_create_daily_limit_error(self):
        """Test creating daily limit error."""
        error = CostLimitExceededError(
            current_cost=10.50,
            limit=10.0,
            limit_type="daily",
        )
        assert error.error_code == "PARACLE-META-005"
        assert "Daily" in str(error)
        assert "$10.50" in str(error)
        assert "$10.00" in str(error)

    def test_create_monthly_limit_error(self):
        """Test creating monthly limit error."""
        error = CostLimitExceededError(
            current_cost=105.0,
            limit=100.0,
            limit_type="monthly",
        )
        assert "Monthly" in str(error)


class TestTemplateNotFoundError:
    """Tests for TemplateNotFoundError."""

    def test_create_template_error(self):
        """Test creating template not found error."""
        error = TemplateNotFoundError("tmpl_security_v1")
        assert error.error_code == "PARACLE-META-006"
        assert "tmpl_security_v1" in str(error)


class TestLearningEngineError:
    """Tests for LearningEngineError."""

    def test_create_learning_error(self):
        """Test creating learning engine error."""
        error = LearningEngineError("Database connection failed")
        assert error.error_code == "PARACLE-META-007"


class TestInvalidArtifactTypeError:
    """Tests for InvalidArtifactTypeError."""

    def test_create_invalid_type_error(self):
        """Test creating invalid artifact type error."""
        error = InvalidArtifactTypeError("unknown_type")
        assert error.error_code == "PARACLE-META-008"
        assert "unknown_type" in str(error)
        assert "agent" in str(error)  # Valid types listed

    def test_create_with_custom_valid_types(self):
        """Test creating with custom valid types list."""
        error = InvalidArtifactTypeError(
            "custom", valid_types=["type_a", "type_b"]
        )
        assert error.details["valid_types"] == ["type_a", "type_b"]


class TestProviderSelectionError:
    """Tests for ProviderSelectionError."""

    def test_create_selection_error(self):
        """Test creating provider selection error."""
        error = ProviderSelectionError(
            reason="No providers available",
            task_type="complex",
        )
        assert error.error_code == "PARACLE-META-009"
        assert "No providers available" in str(error)
        assert error.details["task_type"] == "complex"


class TestFeedbackRecordingError:
    """Tests for FeedbackRecordingError."""

    def test_create_feedback_error(self):
        """Test creating feedback recording error."""
        error = FeedbackRecordingError(
            generation_id="gen_123",
            reason="Generation not found",
        )
        assert error.error_code == "PARACLE-META-010"
        assert "gen_123" in str(error)


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_all_inherit_from_base(self):
        """Test all exceptions inherit from ParacleMetaError."""
        exceptions = [
            ConfigurationError("test"),
            ProviderNotAvailableError("test"),
            GenerationError("agent", "test", "reason"),
            QualityBelowThresholdError("agent", "test", 5.0, 7.0),
            CostLimitExceededError(10.0, 5.0),
            TemplateNotFoundError("test"),
            LearningEngineError("test"),
            InvalidArtifactTypeError("test"),
            ProviderSelectionError("test"),
            FeedbackRecordingError("test", "reason"),
        ]

        for exc in exceptions:
            assert isinstance(exc, ParacleMetaError)
            assert isinstance(exc, Exception)

    def test_unique_error_codes(self):
        """Test all exceptions have unique error codes."""
        exceptions = [
            ParacleMetaError("test"),
            ConfigurationError("test"),
            ProviderNotAvailableError("test"),
            GenerationError("agent", "test", "reason"),
            QualityBelowThresholdError("agent", "test", 5.0, 7.0),
            CostLimitExceededError(10.0, 5.0),
            TemplateNotFoundError("test"),
            LearningEngineError("test"),
            InvalidArtifactTypeError("test"),
            ProviderSelectionError("test"),
            FeedbackRecordingError("test", "reason"),
        ]

        codes = [exc.error_code for exc in exceptions]
        # All codes should be unique
        assert len(codes) == len(set(codes))
