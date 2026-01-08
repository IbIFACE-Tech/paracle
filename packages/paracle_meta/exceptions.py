"""Exceptions for Paracle Meta-Agent Engine.

Error codes:
    PARACLE-META-001: Meta-agent configuration error
    PARACLE-META-002: Provider not available
    PARACLE-META-003: Generation failed
    PARACLE-META-004: Quality score below threshold
    PARACLE-META-005: Cost limit exceeded
    PARACLE-META-006: Template not found
    PARACLE-META-007: Learning engine error
    PARACLE-META-008: Invalid artifact type
    PARACLE-META-009: Provider selection failed
    PARACLE-META-010: Feedback recording failed
"""

from typing import Any


class ParacleMetaError(Exception):
    """Base exception for paracle_meta package."""

    error_code: str = "PARACLE-META-000"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize exception.

        Args:
            message: Human-readable error message
            details: Additional context for debugging
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.details:
            return f"[{self.error_code}] {self.message} | Details: {self.details}"
        return f"[{self.error_code}] {self.message}"


class ConfigurationError(ParacleMetaError):
    """Meta-agent configuration error."""

    error_code = "PARACLE-META-001"


class ProviderNotAvailableError(ParacleMetaError):
    """Requested provider is not available or configured."""

    error_code = "PARACLE-META-002"

    def __init__(
        self,
        provider: str,
        reason: str | None = None,
        available_providers: list[str] | None = None,
    ):
        """Initialize provider not available error.

        Args:
            provider: Name of the unavailable provider
            reason: Why the provider is unavailable
            available_providers: List of providers that are available
        """
        message = f"Provider '{provider}' is not available"
        if reason:
            message += f": {reason}"

        super().__init__(
            message,
            details={
                "provider": provider,
                "reason": reason,
                "available_providers": available_providers or [],
            },
        )


class GenerationError(ParacleMetaError):
    """Artifact generation failed."""

    error_code = "PARACLE-META-003"

    def __init__(
        self,
        artifact_type: str,
        name: str,
        reason: str,
        provider: str | None = None,
    ):
        """Initialize generation error.

        Args:
            artifact_type: Type of artifact being generated
            name: Name of the artifact
            reason: Why generation failed
            provider: Provider that was used
        """
        message = f"Failed to generate {artifact_type} '{name}': {reason}"

        super().__init__(
            message,
            details={
                "artifact_type": artifact_type,
                "name": name,
                "reason": reason,
                "provider": provider,
            },
        )


class QualityBelowThresholdError(ParacleMetaError):
    """Generated artifact quality is below minimum threshold."""

    error_code = "PARACLE-META-004"

    def __init__(
        self,
        artifact_type: str,
        name: str,
        score: float,
        threshold: float,
    ):
        """Initialize quality threshold error.

        Args:
            artifact_type: Type of artifact
            name: Name of the artifact
            score: Actual quality score
            threshold: Required minimum score
        """
        message = (
            f"Quality score {score:.1f} is below threshold {threshold:.1f} "
            f"for {artifact_type} '{name}'"
        )

        super().__init__(
            message,
            details={
                "artifact_type": artifact_type,
                "name": name,
                "score": score,
                "threshold": threshold,
            },
        )


class CostLimitExceededError(ParacleMetaError):
    """Cost limit has been exceeded."""

    error_code = "PARACLE-META-005"

    def __init__(
        self,
        current_cost: float,
        limit: float,
        limit_type: str = "daily",
    ):
        """Initialize cost limit error.

        Args:
            current_cost: Current accumulated cost
            limit: Maximum allowed cost
            limit_type: Type of limit (daily, monthly, total)
        """
        message = (
            f"{limit_type.capitalize()} cost limit exceeded: "
            f"${current_cost:.2f} > ${limit:.2f}"
        )

        super().__init__(
            message,
            details={
                "current_cost": current_cost,
                "limit": limit,
                "limit_type": limit_type,
            },
        )


class TemplateNotFoundError(ParacleMetaError):
    """Template not found in library."""

    error_code = "PARACLE-META-006"

    def __init__(self, template_id: str):
        """Initialize template not found error.

        Args:
            template_id: ID of the missing template
        """
        super().__init__(
            f"Template '{template_id}' not found",
            details={"template_id": template_id},
        )


class LearningEngineError(ParacleMetaError):
    """Error in the learning engine."""

    error_code = "PARACLE-META-007"


class InvalidArtifactTypeError(ParacleMetaError):
    """Invalid artifact type specified."""

    error_code = "PARACLE-META-008"

    def __init__(self, artifact_type: str, valid_types: list[str] | None = None):
        """Initialize invalid artifact type error.

        Args:
            artifact_type: The invalid type
            valid_types: List of valid types
        """
        valid = valid_types or ["agent", "workflow", "skill", "policy"]
        message = f"Invalid artifact type '{artifact_type}'. Valid types: {valid}"

        super().__init__(
            message,
            details={
                "artifact_type": artifact_type,
                "valid_types": valid,
            },
        )


class ProviderSelectionError(ParacleMetaError):
    """Failed to select a suitable provider."""

    error_code = "PARACLE-META-009"

    def __init__(self, reason: str, task_type: str | None = None):
        """Initialize provider selection error.

        Args:
            reason: Why selection failed
            task_type: Type of task being attempted
        """
        message = f"Failed to select provider: {reason}"

        super().__init__(
            message,
            details={
                "reason": reason,
                "task_type": task_type,
            },
        )


class FeedbackRecordingError(ParacleMetaError):
    """Failed to record feedback."""

    error_code = "PARACLE-META-010"

    def __init__(self, generation_id: str, reason: str):
        """Initialize feedback recording error.

        Args:
            generation_id: ID of the generation
            reason: Why recording failed
        """
        message = f"Failed to record feedback for '{generation_id}': {reason}"

        super().__init__(
            message,
            details={
                "generation_id": generation_id,
                "reason": reason,
            },
        )


# Export all exceptions
__all__ = [
    "ParacleMetaError",
    "ConfigurationError",
    "ProviderNotAvailableError",
    "GenerationError",
    "QualityBelowThresholdError",
    "CostLimitExceededError",
    "TemplateNotFoundError",
    "LearningEngineError",
    "InvalidArtifactTypeError",
    "ProviderSelectionError",
    "FeedbackRecordingError",
]
