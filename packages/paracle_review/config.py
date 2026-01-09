"""Review system configuration."""

from typing import Literal

from pydantic import BaseModel, Field

ArtifactType = Literal[
    "file_change", "command_execution", "api_call", "network_request"
]
ReviewTrigger = Literal["all_artifacts", "high_risk_only", "manual"]


class ReviewPolicy(BaseModel):
    """Review trigger policy.

    Defines when human review is required for artifacts.

    Attributes:
        enabled: Enable review workflow
        trigger_mode: When to trigger reviews
        high_risk_patterns: Patterns that trigger high-risk classification
        auto_approve_low_risk: Auto-approve low-risk artifacts
        require_multiple_approvals: Require multiple approvers
        min_approvals: Minimum approvals needed
    """

    enabled: bool = Field(default=True, description="Enable artifact review")

    trigger_mode: ReviewTrigger = Field(
        default="high_risk_only", description="Review trigger mode"
    )

    high_risk_patterns: list[str] = Field(
        default=[
            "*.env",
            "*.key",
            "*.pem",
            "/etc/*",
            "rm -rf",
            "DROP TABLE",
            "DELETE FROM",
        ],
        description="Patterns indicating high-risk artifacts",
    )

    auto_approve_low_risk: bool = Field(
        default=False, description="Auto-approve low-risk artifacts"
    )

    require_multiple_approvals: bool = Field(
        default=False, description="Require multiple approvers"
    )

    min_approvals: int = Field(
        default=1, ge=1, le=10, description="Minimum approvals required"
    )

    review_timeout_hours: int = Field(
        default=24, ge=1, le=168, description="Review timeout in hours"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "enabled": True,
                    "trigger_mode": "high_risk_only",
                    "high_risk_patterns": ["*.env", "rm -rf"],
                    "auto_approve_low_risk": False,
                    "min_approvals": 1,
                }
            ]
        }
    }


class ReviewConfig(BaseModel):
    """Review system configuration.

    Attributes:
        policy: Review policy
        notify_on_review: Send notifications for new reviews
        notification_channels: Notification channels (email, slack, etc.)
        store_artifacts: Store artifact content for review
    """

    policy: ReviewPolicy = Field(
        default_factory=ReviewPolicy, description="Review policy"
    )

    notify_on_review: bool = Field(
        default=True, description="Send notifications for reviews"
    )

    notification_channels: list[str] = Field(
        default=["log"], description="Notification channels"
    )

    store_artifacts: bool = Field(default=True, description="Store artifact content")

    max_artifact_size_mb: int = Field(
        default=10, ge=1, le=100, description="Maximum artifact size to store"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "policy": {"enabled": True, "trigger_mode": "high_risk_only"},
                    "notify_on_review": True,
                    "notification_channels": ["log", "email"],
                }
            ]
        }
    }
