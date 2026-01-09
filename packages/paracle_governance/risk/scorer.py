"""Risk scorer for calculating action risk scores.

This module provides the RiskScorer class that calculates risk scores
for agent actions based on multiple configurable factors.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .factors import (
    ACTION_TYPE_SCORES,
    AGENT_TRUST_SCORES,
    DATA_SENSITIVITY_SCORES,
    DEFAULT_RISK_FACTORS,
    REVERSIBILITY_SCORES,
    DataSensitivity,
    RiskFactor,
    RiskLevel,
)
from .thresholds import RiskAction, RiskThresholds


class RiskScore(BaseModel):
    """Result of risk score calculation."""

    model_config = ConfigDict(frozen=True)

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall risk score (0-100)",
    )
    level: RiskLevel = Field(
        ...,
        description="Risk level based on score",
    )
    action: RiskAction = Field(
        ...,
        description="Recommended action based on risk",
    )
    factor_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Individual factor scores",
    )
    factor_contributions: dict[str, float] = Field(
        default_factory=dict,
        description="Weighted contribution of each factor",
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether approval is required",
    )
    approval_roles: list[str] = Field(
        default_factory=list,
        description="Roles that can approve (if approval required)",
    )
    justification_required: bool = Field(
        default=False,
        description="Whether justification is required",
    )
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the score was calculated",
    )
    context_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of context used for calculation",
    )


class RiskScorer:
    """Calculates risk scores for agent actions.

    The scorer evaluates multiple risk factors to produce an overall
    risk score, level, and recommended action.

    Example:
        >>> scorer = RiskScorer()
        >>> result = scorer.calculate(
        ...     action="write_file",
        ...     agent="coder",
        ...     context={
        ...         "data_sensitivity": "pii",
        ...         "path": "/data/users.json",
        ...     }
        ... )
        >>> print(f"Risk: {result.score:.1f} ({result.level.value})")
        >>> print(f"Action: {result.action.value}")
    """

    def __init__(
        self,
        *,
        factors: dict[str, RiskFactor] | None = None,
        thresholds: RiskThresholds | None = None,
    ):
        """Initialize the risk scorer.

        Args:
            factors: Custom risk factors. Uses defaults if not provided.
            thresholds: Custom risk thresholds. Uses defaults if not provided.
        """
        self._factors = factors or dict(DEFAULT_RISK_FACTORS)
        self._thresholds = thresholds or RiskThresholds()

    @property
    def factors(self) -> dict[str, RiskFactor]:
        """Get the configured risk factors."""
        return self._factors

    @property
    def thresholds(self) -> RiskThresholds:
        """Get the configured risk thresholds."""
        return self._thresholds

    def add_factor(self, factor: RiskFactor) -> None:
        """Add or update a risk factor.

        Args:
            factor: The risk factor to add.
        """
        self._factors[factor.id] = factor

    def remove_factor(self, factor_id: str) -> bool:
        """Remove a risk factor.

        Args:
            factor_id: ID of the factor to remove.

        Returns:
            True if removed, False if not found.
        """
        if factor_id in self._factors:
            del self._factors[factor_id]
            return True
        return False

    def calculate(
        self,
        action: str,
        *,
        agent: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> RiskScore:
        """Calculate the risk score for an action.

        Args:
            action: The action being performed.
            agent: The agent performing the action.
            context: Additional context for risk calculation.

        Returns:
            RiskScore with the calculated score and metadata.
        """
        context = context or {}

        factor_scores: dict[str, float] = {}
        factor_contributions: dict[str, float] = {}
        total_weight = 0.0
        weighted_sum = 0.0

        for factor_id, factor in self._factors.items():
            if not factor.enabled:
                continue

            # Calculate individual factor score
            factor_score = self._calculate_factor_score(
                factor_id, action, agent, context
            )
            factor_scores[factor_id] = factor_score

            # Calculate weighted contribution
            contribution = (factor_score / factor.max_score) * factor.weight * 100
            contribution = min(contribution, factor.max_score)  # Cap contribution
            factor_contributions[factor_id] = contribution

            # Accumulate for weighted average
            total_weight += factor.weight
            weighted_sum += (factor_score / factor.max_score) * factor.weight

        # Calculate overall score (normalized 0-100)
        if total_weight > 0:
            overall_score = (weighted_sum / total_weight) * 100
        else:
            overall_score = 0.0

        # Clamp to 0-100
        overall_score = max(0.0, min(100.0, overall_score))

        # Determine level and action from thresholds
        level = self._thresholds.get_level_for_score(overall_score)
        threshold_action = self._thresholds.get_action_for_score(overall_score)
        requires_approval = self._thresholds.requires_approval(overall_score)
        approval_roles = self._thresholds.get_approval_roles(overall_score)

        threshold = self._thresholds.get_threshold_for_score(overall_score)
        justification_required = threshold.require_justification if threshold else False

        return RiskScore(
            score=overall_score,
            level=level,
            action=threshold_action,
            factor_scores=factor_scores,
            factor_contributions=factor_contributions,
            requires_approval=requires_approval,
            approval_roles=approval_roles,
            justification_required=justification_required,
            context_summary={
                "action": action,
                "agent": agent,
                "factors_evaluated": list(factor_scores.keys()),
            },
        )

    def _calculate_factor_score(
        self,
        factor_id: str,
        action: str,
        agent: str | None,
        context: dict[str, Any],
    ) -> float:
        """Calculate the score for a specific factor.

        Args:
            factor_id: ID of the factor.
            action: The action being performed.
            agent: The agent performing the action.
            context: Additional context.

        Returns:
            Factor score (0-100).
        """
        if factor_id == "data_sensitivity":
            return self._score_data_sensitivity(context)
        elif factor_id == "action_type":
            return self._score_action_type(action)
        elif factor_id == "agent_trust":
            return self._score_agent_trust(agent, context)
        elif factor_id == "historical_behavior":
            return self._score_historical_behavior(agent, context)
        elif factor_id == "time_of_day":
            return self._score_time_of_day(context)
        elif factor_id == "resource_scope":
            return self._score_resource_scope(context)
        elif factor_id == "external_dependency":
            return self._score_external_dependency(action, context)
        elif factor_id == "reversibility":
            return self._score_reversibility(action, context)
        else:
            # Unknown factor - return neutral score
            return 50.0

    def _score_data_sensitivity(self, context: dict[str, Any]) -> float:
        """Calculate data sensitivity score."""
        sensitivity = context.get("data_sensitivity")

        if isinstance(sensitivity, DataSensitivity):
            return DATA_SENSITIVITY_SCORES.get(sensitivity, 50.0)
        elif isinstance(sensitivity, str):
            try:
                sens_enum = DataSensitivity(sensitivity.lower())
                return DATA_SENSITIVITY_SCORES.get(sens_enum, 50.0)
            except ValueError:
                pass

        # Check for specific data type indicators
        path = context.get("path", "")
        if any(x in path.lower() for x in ["pii", "personal", "user", "customer"]):
            return DATA_SENSITIVITY_SCORES[DataSensitivity.PII]
        elif any(x in path.lower() for x in ["financial", "payment", "invoice"]):
            return DATA_SENSITIVITY_SCORES[DataSensitivity.FINANCIAL]
        elif any(x in path.lower() for x in ["secret", "key", "password", "token"]):
            return DATA_SENSITIVITY_SCORES[DataSensitivity.SECRET]

        return DATA_SENSITIVITY_SCORES[DataSensitivity.INTERNAL]

    def _score_action_type(self, action: str) -> float:
        """Calculate action type score."""
        # Normalize action name
        action_lower = action.lower().replace("_", " ").replace("-", " ")

        # Direct lookup
        if action_lower in ACTION_TYPE_SCORES:
            return ACTION_TYPE_SCORES[action_lower]

        # Pattern matching
        if "delete" in action_lower or "remove" in action_lower:
            return ACTION_TYPE_SCORES["delete"]
        elif "write" in action_lower or "create" in action_lower:
            return ACTION_TYPE_SCORES["write"]
        elif "execute" in action_lower or "run" in action_lower:
            return ACTION_TYPE_SCORES["execute"]
        elif "read" in action_lower or "get" in action_lower:
            return ACTION_TYPE_SCORES["read"]
        elif "modify" in action_lower or "update" in action_lower:
            return ACTION_TYPE_SCORES["update"]

        return 50.0  # Default neutral score

    def _score_agent_trust(self, agent: str | None, context: dict[str, Any]) -> float:
        """Calculate agent trust score."""
        # Check explicit trust level in context
        trust_level = context.get("agent_trust_level") or context.get("trust_level")

        if trust_level:
            trust_str = str(trust_level).lower()
            if trust_str in AGENT_TRUST_SCORES:
                return AGENT_TRUST_SCORES[trust_str]

        # Check agent-specific trust from context
        agent_config = context.get("agent", {})
        if isinstance(agent_config, dict):
            agent_trust = agent_config.get("trust_level")
            if agent_trust and str(agent_trust).lower() in AGENT_TRUST_SCORES:
                return AGENT_TRUST_SCORES[str(agent_trust).lower()]

        # Default to medium trust
        return AGENT_TRUST_SCORES["medium"]

    def _score_historical_behavior(
        self, agent: str | None, context: dict[str, Any]
    ) -> float:
        """Calculate historical behavior score."""
        # Look for historical data in context
        history = context.get("agent_history", {})

        if isinstance(history, dict):
            success_rate = history.get("success_rate", 0.95)
            recent_failures = history.get("recent_failures", 0)

            # Higher success rate = lower risk
            base_score = (1 - success_rate) * 100

            # Recent failures increase risk
            failure_penalty = min(recent_failures * 10, 50)

            return min(base_score + failure_penalty, 100)

        # No history available - neutral score
        return 25.0

    def _score_time_of_day(self, context: dict[str, Any]) -> float:
        """Calculate time-of-day risk score."""
        # Check if outside business hours
        current_hour = context.get("current_hour")
        if current_hour is None:
            current_hour = datetime.now().hour

        # Business hours: 8 AM - 6 PM
        if 8 <= current_hour <= 18:
            return 10.0  # Low risk during business hours
        elif 6 <= current_hour < 8 or 18 < current_hour <= 22:
            return 30.0  # Medium risk during edge hours
        else:
            return 60.0  # Higher risk during night hours

    def _score_resource_scope(self, context: dict[str, Any]) -> float:
        """Calculate resource scope score."""
        scope = context.get("resource_scope", "single")
        affected_count = context.get("affected_resources", 1)

        # Scope-based scoring
        scope_scores = {
            "single": 20.0,
            "multiple": 50.0,
            "directory": 60.0,
            "project": 70.0,
            "system": 90.0,
        }

        base_score = scope_scores.get(scope, 50.0)

        # Adjust based on count
        if affected_count > 100:
            base_score = min(base_score + 20, 100)
        elif affected_count > 10:
            base_score = min(base_score + 10, 100)

        return base_score

    def _score_external_dependency(self, action: str, context: dict[str, Any]) -> float:
        """Calculate external dependency score."""
        is_external = context.get("is_external", False)
        external_service = context.get("external_service")

        if not is_external and not external_service:
            # Check action name for external indicators
            if any(x in action.lower() for x in ["api", "http", "external", "remote"]):
                is_external = True

        if is_external:
            # External calls have inherent risk
            if context.get("is_authenticated", False):
                return 40.0  # Authenticated external call
            else:
                return 70.0  # Unauthenticated external call

        return 10.0  # Internal operation

    def _score_reversibility(self, action: str, context: dict[str, Any]) -> float:
        """Calculate reversibility score."""
        reversibility = context.get("reversibility")

        if reversibility:
            rev_str = str(reversibility).lower().replace(" ", "_")
            if rev_str in REVERSIBILITY_SCORES:
                return REVERSIBILITY_SCORES[rev_str]

        # Infer from action type
        action_lower = action.lower()
        if "delete" in action_lower or "drop" in action_lower:
            return REVERSIBILITY_SCORES["irreversible"]
        elif "write" in action_lower or "create" in action_lower:
            return REVERSIBILITY_SCORES["partially_reversible"]
        elif "update" in action_lower or "modify" in action_lower:
            return REVERSIBILITY_SCORES["partially_reversible"]
        elif "read" in action_lower or "get" in action_lower:
            return REVERSIBILITY_SCORES["fully_reversible"]

        return 50.0  # Unknown reversibility

    def get_factor_details(self) -> list[dict[str, Any]]:
        """Get details about all configured factors.

        Returns:
            List of factor details.
        """
        return [
            {
                "id": f.id,
                "name": f.name,
                "description": f.description,
                "weight": f.weight,
                "max_score": f.max_score,
                "enabled": f.enabled,
                "iso_control": f.iso_control,
            }
            for f in self._factors.values()
        ]
