"""Risk factors and levels for governance.

This module defines the risk assessment framework including
risk levels, data sensitivity classifications, and risk factors.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    """Risk severity levels for agent actions.

    Aligned with ISO 42001 risk assessment requirements.
    """

    LOW = "low"
    """Low risk (0-30): Auto-approve, minimal logging."""

    MEDIUM = "medium"
    """Medium risk (31-60): Audit required, standard logging."""

    HIGH = "high"
    """High risk (61-80): Approval required, detailed logging."""

    CRITICAL = "critical"
    """Critical risk (81-100): Multi-approval + escalation, full audit."""

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        """Determine risk level from a numeric score.

        Args:
            score: Risk score (0-100).

        Returns:
            Corresponding RiskLevel.
        """
        if score <= 30:
            return cls.LOW
        elif score <= 60:
            return cls.MEDIUM
        elif score <= 80:
            return cls.HIGH
        else:
            return cls.CRITICAL


class DataSensitivity(str, Enum):
    """Data sensitivity classifications.

    Used for determining risk based on data being accessed or modified.
    """

    PUBLIC = "public"
    """Publicly available data."""

    INTERNAL = "internal"
    """Internal business data."""

    CONFIDENTIAL = "confidential"
    """Confidential data requiring access controls."""

    PII = "pii"
    """Personally Identifiable Information (GDPR/privacy)."""

    FINANCIAL = "financial"
    """Financial data (PCI-DSS relevant)."""

    HEALTH = "health"
    """Health data (HIPAA relevant)."""

    SECRET = "secret"
    """Highly sensitive secrets (API keys, passwords)."""


class RiskFactor(BaseModel):
    """A factor that contributes to risk score calculation.

    Risk factors are combined to calculate the overall risk score
    for an action. Each factor has a weight and a scoring function.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Unique factor identifier",
    )
    name: str = Field(
        ...,
        description="Human-readable factor name",
    )
    description: str = Field(
        default="",
        description="Detailed description of the factor",
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Weight of this factor in overall score (0-10)",
    )
    max_score: float = Field(
        default=100.0,
        ge=0.0,
        description="Maximum score this factor can contribute",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this factor is active",
    )
    iso_control: str | None = Field(
        default=None,
        description="Related ISO 42001 control",
    )


# Pre-defined risk factors
DEFAULT_RISK_FACTORS = {
    # Data sensitivity factor
    "data_sensitivity": RiskFactor(
        id="data_sensitivity",
        name="Data Sensitivity",
        description="Risk based on the sensitivity classification of data being accessed",
        weight=3.0,
        max_score=100.0,
        iso_control="6.1",
    ),
    # Action type factor
    "action_type": RiskFactor(
        id="action_type",
        name="Action Type",
        description="Risk based on the type of action (read, write, delete, execute)",
        weight=2.5,
        max_score=100.0,
        iso_control="8.1",
    ),
    # Agent trust level factor
    "agent_trust": RiskFactor(
        id="agent_trust",
        name="Agent Trust Level",
        description="Risk based on the trust level of the executing agent",
        weight=2.0,
        max_score=100.0,
        iso_control="7.2",
    ),
    # Historical behavior factor
    "historical_behavior": RiskFactor(
        id="historical_behavior",
        name="Historical Behavior",
        description="Risk based on agent's historical success/failure rates",
        weight=1.5,
        max_score=50.0,
        iso_control="9.1",
    ),
    # Time of day factor
    "time_of_day": RiskFactor(
        id="time_of_day",
        name="Time of Day",
        description="Risk based on unusual timing (off-hours operations)",
        weight=1.0,
        max_score=30.0,
        iso_control="9.2",
    ),
    # Resource scope factor
    "resource_scope": RiskFactor(
        id="resource_scope",
        name="Resource Scope",
        description="Risk based on the scope of resources affected",
        weight=2.0,
        max_score=80.0,
        iso_control="8.2",
    ),
    # External dependency factor
    "external_dependency": RiskFactor(
        id="external_dependency",
        name="External Dependency",
        description="Risk when action involves external systems or APIs",
        weight=1.5,
        max_score=60.0,
        iso_control="6.2",
    ),
    # Reversibility factor
    "reversibility": RiskFactor(
        id="reversibility",
        name="Reversibility",
        description="Risk based on whether the action can be undone",
        weight=2.0,
        max_score=80.0,
        iso_control="10.1",
    ),
}


# Scoring tables for different factors

# Data sensitivity scores (0-100)
DATA_SENSITIVITY_SCORES: dict[DataSensitivity, float] = {
    DataSensitivity.PUBLIC: 10.0,
    DataSensitivity.INTERNAL: 30.0,
    DataSensitivity.CONFIDENTIAL: 50.0,
    DataSensitivity.PII: 80.0,
    DataSensitivity.FINANCIAL: 85.0,
    DataSensitivity.HEALTH: 90.0,
    DataSensitivity.SECRET: 100.0,
}

# Action type scores (0-100)
ACTION_TYPE_SCORES: dict[str, float] = {
    "read": 20.0,
    "list": 15.0,
    "search": 15.0,
    "write": 50.0,
    "create": 45.0,
    "update": 55.0,
    "delete": 80.0,
    "execute": 70.0,
    "install": 75.0,
    "modify_config": 85.0,
    "access_secrets": 95.0,
}

# Agent trust level scores (0-100, higher trust = lower risk)
AGENT_TRUST_SCORES: dict[str, float] = {
    "untrusted": 100.0,
    "low": 70.0,
    "medium": 40.0,
    "high": 20.0,
    "trusted": 10.0,
    "system": 5.0,
}

# Reversibility scores (0-100, more reversible = lower risk)
REVERSIBILITY_SCORES: dict[str, float] = {
    "fully_reversible": 10.0,
    "partially_reversible": 40.0,
    "difficult_to_reverse": 70.0,
    "irreversible": 100.0,
}
