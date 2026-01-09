"""Rollback configuration."""

from typing import Literal

from pydantic import BaseModel, Field

RollbackTrigger = Literal["on_error", "on_timeout", "on_limit_exceeded", "manual"]


class RollbackPolicy(BaseModel):
    """Rollback trigger policy.

    Defines when automatic rollback should occur.

    Attributes:
        enabled: Enable automatic rollback
        triggers: Events that trigger rollback
        max_snapshots: Maximum snapshots to keep per sandbox
        snapshot_retention_hours: How long to keep snapshots
    """

    enabled: bool = Field(default=True, description="Enable automatic rollback")

    triggers: list[RollbackTrigger] = Field(
        default=["on_error", "on_timeout", "on_limit_exceeded"],
        description="Events that trigger rollback",
    )

    max_snapshots: int = Field(
        default=5, ge=1, le=20, description="Maximum snapshots per sandbox"
    )

    snapshot_retention_hours: int = Field(
        default=24, ge=1, le=168, description="Snapshot retention period"  # 1 week
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "enabled": True,
                    "triggers": ["on_error", "on_timeout"],
                    "max_snapshots": 5,
                    "snapshot_retention_hours": 24,
                }
            ]
        }
    }


class RollbackConfig(BaseModel):
    """Rollback system configuration.

    Attributes:
        policy: Rollback policy
        snapshot_compression: Compress snapshots
        verify_after_restore: Verify filesystem after restore
        backup_before_rollback: Create backup before rollback
    """

    policy: RollbackPolicy = Field(
        default_factory=RollbackPolicy, description="Rollback policy"
    )

    snapshot_compression: bool = Field(
        default=True, description="Compress snapshots to save space"
    )

    verify_after_restore: bool = Field(
        default=True, description="Verify filesystem after restore"
    )

    backup_before_rollback: bool = Field(
        default=False, description="Create backup before rolling back"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "policy": {
                        "enabled": True,
                        "triggers": ["on_error"],
                        "max_snapshots": 3,
                    },
                    "snapshot_compression": True,
                    "verify_after_restore": True,
                }
            ]
        }
    }
