"""Risk thresholds and actions configuration.

This module defines configurable thresholds for risk levels
and the actions to take when thresholds are crossed.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .factors import RiskLevel


class RiskAction(str, Enum):
    """Actions to take based on risk level."""

    ALLOW = "allow"
    """Allow the action to proceed."""

    AUDIT = "audit"
    """Allow but create audit record."""

    WARN = "warn"
    """Allow but emit warning."""

    REQUIRE_APPROVAL = "require_approval"
    """Require human approval before proceeding."""

    ESCALATE = "escalate"
    """Escalate to higher authority."""

    DENY = "deny"
    """Deny the action."""


class RiskThreshold(BaseModel):
    """Configuration for a single risk threshold."""

    model_config = ConfigDict(frozen=True)

    min_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Minimum score for this threshold",
    )
    max_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Maximum score for this threshold",
    )
    level: RiskLevel = Field(
        ...,
        description="Risk level name",
    )
    action: RiskAction = Field(
        ...,
        description="Action to take for this risk level",
    )
    require_justification: bool = Field(
        default=False,
        description="Whether a justification is required",
    )
    notification_channels: list[str] = Field(
        default_factory=list,
        description="Channels to notify (email, slack, etc.)",
    )
    approval_roles: list[str] = Field(
        default_factory=list,
        description="Roles that can approve (if action=require_approval)",
    )
    escalation_timeout_minutes: int | None = Field(
        default=None,
        description="Minutes before auto-escalation (if action=escalate)",
    )


class RiskThresholds(BaseModel):
    """Configuration for all risk thresholds.

    Defines the boundaries between risk levels and the actions
    to take for each level.
    """

    model_config = ConfigDict(frozen=False)

    thresholds: list[RiskThreshold] = Field(
        default_factory=list,
        description="List of threshold configurations",
    )
    default_action: RiskAction = Field(
        default=RiskAction.ALLOW,
        description="Default action when no threshold matches",
    )

    def __init__(self, **data):
        super().__init__(**data)
        if not self.thresholds:
            self.thresholds = self._default_thresholds()

    def _default_thresholds(self) -> list[RiskThreshold]:
        """Create default threshold configuration."""
        return [
            RiskThreshold(
                min_score=0.0,
                max_score=30.0,
                level=RiskLevel.LOW,
                action=RiskAction.ALLOW,
                require_justification=False,
            ),
            RiskThreshold(
                min_score=30.01,
                max_score=60.0,
                level=RiskLevel.MEDIUM,
                action=RiskAction.AUDIT,
                require_justification=False,
                notification_channels=["log"],
            ),
            RiskThreshold(
                min_score=60.01,
                max_score=80.0,
                level=RiskLevel.HIGH,
                action=RiskAction.REQUIRE_APPROVAL,
                require_justification=True,
                notification_channels=["log", "email"],
                approval_roles=["admin", "security"],
            ),
            RiskThreshold(
                min_score=80.01,
                max_score=100.0,
                level=RiskLevel.CRITICAL,
                action=RiskAction.ESCALATE,
                require_justification=True,
                notification_channels=["log", "email", "slack"],
                approval_roles=["admin", "security", "executive"],
                escalation_timeout_minutes=15,
            ),
        ]

    def get_threshold_for_score(self, score: float) -> RiskThreshold | None:
        """Get the threshold configuration for a given score.

        Args:
            score: Risk score (0-100).

        Returns:
            Matching threshold or None.
        """
        for threshold in self.thresholds:
            if threshold.min_score <= score <= threshold.max_score:
                return threshold
        return None

    def get_action_for_score(self, score: float) -> RiskAction:
        """Get the action to take for a given score.

        Args:
            score: Risk score (0-100).

        Returns:
            Action to take.
        """
        threshold = self.get_threshold_for_score(score)
        if threshold:
            return threshold.action
        return self.default_action

    def get_level_for_score(self, score: float) -> RiskLevel:
        """Get the risk level for a given score.

        Args:
            score: Risk score (0-100).

        Returns:
            Risk level.
        """
        threshold = self.get_threshold_for_score(score)
        if threshold:
            return threshold.level
        return RiskLevel.from_score(score)

    def requires_approval(self, score: float) -> bool:
        """Check if a score requires approval.

        Args:
            score: Risk score (0-100).

        Returns:
            True if approval is required.
        """
        action = self.get_action_for_score(score)
        return action in (RiskAction.REQUIRE_APPROVAL, RiskAction.ESCALATE)

    def get_approval_roles(self, score: float) -> list[str]:
        """Get the roles that can approve for a given score.

        Args:
            score: Risk score (0-100).

        Returns:
            List of approval roles.
        """
        threshold = self.get_threshold_for_score(score)
        if threshold:
            return threshold.approval_roles
        return []

    def update_threshold(
        self,
        level: RiskLevel,
        *,
        min_score: float | None = None,
        max_score: float | None = None,
        action: RiskAction | None = None,
        approval_roles: list[str] | None = None,
    ) -> bool:
        """Update a threshold configuration.

        Args:
            level: Risk level to update.
            min_score: New minimum score.
            max_score: New maximum score.
            action: New action.
            approval_roles: New approval roles.

        Returns:
            True if threshold was found and updated.
        """
        for i, threshold in enumerate(self.thresholds):
            if threshold.level == level:
                # Create new threshold with updated values
                new_threshold = RiskThreshold(
                    min_score=(
                        min_score if min_score is not None else threshold.min_score
                    ),
                    max_score=(
                        max_score if max_score is not None else threshold.max_score
                    ),
                    level=threshold.level,
                    action=action if action is not None else threshold.action,
                    require_justification=threshold.require_justification,
                    notification_channels=threshold.notification_channels,
                    approval_roles=(
                        approval_roles
                        if approval_roles is not None
                        else threshold.approval_roles
                    ),
                    escalation_timeout_minutes=threshold.escalation_timeout_minutes,
                )
                self.thresholds[i] = new_threshold
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert thresholds to a dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "thresholds": [
                {
                    "level": t.level.value,
                    "min_score": t.min_score,
                    "max_score": t.max_score,
                    "action": t.action.value,
                    "require_justification": t.require_justification,
                    "approval_roles": t.approval_roles,
                }
                for t in self.thresholds
            ],
            "default_action": self.default_action.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RiskThresholds":
        """Create thresholds from a dictionary.

        Args:
            data: Dictionary with threshold data.

        Returns:
            RiskThresholds instance.
        """
        thresholds = []
        for t_data in data.get("thresholds", []):
            thresholds.append(
                RiskThreshold(
                    min_score=t_data["min_score"],
                    max_score=t_data["max_score"],
                    level=RiskLevel(t_data["level"]),
                    action=RiskAction(t_data["action"]),
                    require_justification=t_data.get("require_justification", False),
                    approval_roles=t_data.get("approval_roles", []),
                )
            )

        return cls(
            thresholds=thresholds,
            default_action=RiskAction(data.get("default_action", "allow")),
        )
