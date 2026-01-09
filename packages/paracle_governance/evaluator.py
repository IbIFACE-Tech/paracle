"""Policy evaluator for governance decisions.

This module provides the core evaluation logic for determining whether
an action is allowed, denied, or requires approval based on active policies.
"""

import time
from typing import Any

from .exceptions import PolicyEvaluationError, PolicyViolationError
from .policies import Policy, PolicyResult, PolicyType


class PolicyEvaluator:
    """Evaluates policies against actions and contexts.

    The evaluator processes policies in priority order and applies
    the appropriate policy type logic (allow, deny, require_approval, etc.).

    Conflict Resolution:
    - Policies are evaluated in priority order (highest first)
    - DENY policies take precedence over ALLOW at the same priority
    - First matching policy determines the outcome
    - If no policies match, the default action is to allow

    Example:
        >>> evaluator = PolicyEvaluator()
        >>> evaluator.add_policy(deny_policy)
        >>> evaluator.add_policy(allow_policy)
        >>> result = evaluator.evaluate("write_file", {"agent": {"name": "coder"}})
        >>> print(result.allowed)
    """

    def __init__(self, default_allow: bool = True):
        """Initialize the policy evaluator.

        Args:
            default_allow: Default action when no policies match.
                          True = allow, False = deny.
        """
        self._policies: dict[str, Policy] = {}
        self._default_allow = default_allow

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the evaluator.

        Args:
            policy: The policy to add.
        """
        self._policies[policy.id] = policy

    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy from the evaluator.

        Args:
            policy_id: ID of the policy to remove.

        Returns:
            True if the policy was removed, False if not found.
        """
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def get_policy(self, policy_id: str) -> Policy | None:
        """Get a policy by ID.

        Args:
            policy_id: ID of the policy to retrieve.

        Returns:
            The policy if found, None otherwise.
        """
        return self._policies.get(policy_id)

    def list_policies(self, enabled_only: bool = True) -> list[Policy]:
        """List all policies.

        Args:
            enabled_only: If True, only return enabled policies.

        Returns:
            List of policies sorted by priority (highest first).
        """
        policies = list(self._policies.values())
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        return sorted(policies, key=lambda p: p.priority, reverse=True)

    def evaluate(
        self,
        action: str,
        context: dict[str, Any] | None = None,
        *,
        agent: str | None = None,
        risk_score: float | None = None,
    ) -> PolicyResult:
        """Evaluate policies for an action.

        Args:
            action: The action being performed.
            context: Context data for condition evaluation.
            agent: Optional agent name for context.
            risk_score: Optional pre-calculated risk score.

        Returns:
            PolicyResult with the evaluation outcome.

        Raises:
            PolicyEvaluationError: If evaluation fails due to an error.
        """
        start_time = time.perf_counter()
        context = context or {}

        # Add agent to context if provided
        if agent and "agent" not in context:
            context["agent"] = {"name": agent}

        evaluated_policies: list[str] = []
        matching_deny: Policy | None = None
        matching_require_approval: Policy | None = None
        matching_audit: Policy | None = None
        matching_allow: Policy | None = None

        # Get policies sorted by priority
        sorted_policies = self.list_policies(enabled_only=True)

        for policy in sorted_policies:
            try:
                # Check if policy applies to this action
                if not policy.matches_action(action):
                    continue

                evaluated_policies.append(policy.id)

                # Check if all conditions are met
                if not policy.evaluate_conditions(context):
                    continue

                # Categorize by type
                if policy.type == PolicyType.DENY:
                    if (
                        matching_deny is None
                        or policy.priority > matching_deny.priority
                    ):
                        matching_deny = policy
                elif policy.type == PolicyType.REQUIRE_APPROVAL:
                    if (
                        matching_require_approval is None
                        or policy.priority > matching_require_approval.priority
                    ):
                        matching_require_approval = policy
                elif policy.type == PolicyType.AUDIT:
                    if (
                        matching_audit is None
                        or policy.priority > matching_audit.priority
                    ):
                        matching_audit = policy
                elif policy.type == PolicyType.ALLOW:
                    if (
                        matching_allow is None
                        or policy.priority > matching_allow.priority
                    ):
                        matching_allow = policy

            except Exception as e:
                raise PolicyEvaluationError(
                    f"Error evaluating policy: {e}",
                    policy_id=policy.id,
                ) from e

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Determine outcome based on policy type precedence
        # DENY > REQUIRE_APPROVAL > AUDIT > ALLOW > default

        if matching_deny:
            return PolicyResult(
                allowed=False,
                policy_id=matching_deny.id,
                policy_type=matching_deny.type,
                reason=f"Action denied by policy: {matching_deny.name}",
                requires_approval=False,
                risk_score=risk_score,
                audit_required=matching_audit is not None,
                evaluated_policies=evaluated_policies,
                evaluation_time_ms=elapsed_ms,
            )

        if matching_require_approval:
            return PolicyResult(
                allowed=True,  # Allowed but requires approval
                policy_id=matching_require_approval.id,
                policy_type=matching_require_approval.type,
                reason=f"Action requires approval: {matching_require_approval.name}",
                requires_approval=True,
                approval_roles=matching_require_approval.approval_required_by,
                risk_score=risk_score,
                audit_required=True,  # Always audit approval-required actions
                evaluated_policies=evaluated_policies,
                evaluation_time_ms=elapsed_ms,
            )

        if matching_audit:
            return PolicyResult(
                allowed=True,
                policy_id=matching_audit.id,
                policy_type=matching_audit.type,
                reason=f"Action allowed with audit: {matching_audit.name}",
                requires_approval=False,
                risk_score=risk_score,
                audit_required=True,
                evaluated_policies=evaluated_policies,
                evaluation_time_ms=elapsed_ms,
            )

        if matching_allow:
            return PolicyResult(
                allowed=True,
                policy_id=matching_allow.id,
                policy_type=matching_allow.type,
                reason=f"Action explicitly allowed: {matching_allow.name}",
                requires_approval=False,
                risk_score=risk_score,
                audit_required=False,
                evaluated_policies=evaluated_policies,
                evaluation_time_ms=elapsed_ms,
            )

        # No matching policies - use default
        return PolicyResult(
            allowed=self._default_allow,
            policy_id=None,
            policy_type=None,
            reason=(
                "No matching policies - default allow"
                if self._default_allow
                else "No matching policies - default deny"
            ),
            requires_approval=False,
            risk_score=risk_score,
            audit_required=False,
            evaluated_policies=evaluated_policies,
            evaluation_time_ms=elapsed_ms,
        )

    def check_and_raise(
        self,
        action: str,
        context: dict[str, Any] | None = None,
        *,
        agent: str | None = None,
    ) -> PolicyResult:
        """Evaluate policies and raise exception if denied.

        This is a convenience method that combines evaluation with
        automatic exception raising for denied actions.

        Args:
            action: The action being performed.
            context: Context data for condition evaluation.
            agent: Optional agent name for context.

        Returns:
            PolicyResult if action is allowed.

        Raises:
            PolicyViolationError: If the action is denied.
        """
        result = self.evaluate(action, context, agent=agent)

        if not result.allowed:
            raise PolicyViolationError(
                policy_id=result.policy_id or "unknown",
                action=action,
                reason=result.reason,
                agent=agent,
                risk_score=result.risk_score,
            )

        return result

    def get_applicable_policies(
        self,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> list[Policy]:
        """Get all policies that apply to an action.

        This is useful for previewing which policies would be evaluated
        without actually making a decision.

        Args:
            action: The action to check.
            context: Context data for condition evaluation.

        Returns:
            List of applicable policies sorted by priority.
        """
        context = context or {}
        applicable = []

        for policy in self.list_policies(enabled_only=True):
            if policy.matches_action(action):
                if policy.evaluate_conditions(context):
                    applicable.append(policy)

        return applicable
