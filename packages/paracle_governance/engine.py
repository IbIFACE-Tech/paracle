"""Policy Engine - Main governance interface.

This module provides the high-level PolicyEngine class that orchestrates
policy loading, evaluation, and enforcement for the governance layer.
"""

import logging
from pathlib import Path
from typing import Any

from .policies import DEFAULT_POLICIES, Policy, PolicyResult

logger = logging.getLogger(__name__)

from .evaluator import PolicyEvaluator  # noqa: E402
from .exceptions import PolicyNotFoundError, PolicyViolationError  # noqa: E402
from .loader import PolicyLoader  # noqa: E402


class PolicyEngine:
    """High-level governance policy engine.

    The PolicyEngine is the main interface for governance operations.
    It manages policy loading, evaluation, and enforcement, providing
    a unified API for the governance layer.

    Features:
    - Load policies from YAML files or directories
    - Evaluate actions against active policies
    - Enforce policies with automatic exception raising
    - Integrate with risk scoring and approval workflows
    - Provide audit hooks for compliance logging

    Example:
        >>> engine = PolicyEngine()
        >>> engine.load_default_policies()
        >>> engine.load_policies("custom_policies.yaml")
        >>>
        >>> # Check if action is allowed
        >>> result = engine.evaluate("write_file", context={"path": "/etc/passwd"})
        >>> if not result.allowed:
        ...     print(f"Denied: {result.reason}")
        >>>
        >>> # Enforce with exception
        >>> engine.enforce("read_file", context={"path": "/tmp/data.txt"})
    """

    def __init__(
        self,
        *,
        default_allow: bool = True,
        load_defaults: bool = False,
        policy_path: Path | str | None = None,
    ):
        """Initialize the policy engine.

        Args:
            default_allow: Default action when no policies match.
            load_defaults: Whether to load default built-in policies.
            policy_path: Path to load policies from (file or directory).
        """
        self._evaluator = PolicyEvaluator(default_allow=default_allow)
        self._loader = PolicyLoader()
        self._audit_hooks: list[callable] = []

        if load_defaults:
            self.load_default_policies()

        if policy_path:
            self.load_policies(policy_path)

    def load_default_policies(self) -> int:
        """Load the default built-in policies.

        Returns:
            Number of policies loaded.
        """
        count = 0
        for policy in DEFAULT_POLICIES.values():
            self._evaluator.add_policy(policy)
            count += 1
        return count

    def load_policies(self, path: Path | str) -> int:
        """Load policies from a file or directory.

        Args:
            path: Path to a YAML file or directory of YAML files.

        Returns:
            Number of policies loaded.
        """
        path = Path(path)

        if path.is_dir():
            policies = self._loader.load_directory(path)
        else:
            policies = self._loader.load_file(path)

        for policy in policies:
            self._evaluator.add_policy(policy)

        return len(policies)

    def load_policies_from_string(self, yaml_string: str) -> int:
        """Load policies from a YAML string.

        Args:
            yaml_string: YAML content as a string.

        Returns:
            Number of policies loaded.
        """
        policies = self._loader.load_string(yaml_string)

        for policy in policies:
            self._evaluator.add_policy(policy)

        return len(policies)

    def add_policy(self, policy: Policy) -> None:
        """Add a single policy to the engine.

        Args:
            policy: The policy to add.
        """
        self._evaluator.add_policy(policy)

    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy from the engine.

        Args:
            policy_id: ID of the policy to remove.

        Returns:
            True if removed, False if not found.
        """
        return self._evaluator.remove_policy(policy_id)

    def get_policy(self, policy_id: str) -> Policy:
        """Get a policy by ID.

        Args:
            policy_id: ID of the policy.

        Returns:
            The policy.

        Raises:
            PolicyNotFoundError: If policy doesn't exist.
        """
        policy = self._evaluator.get_policy(policy_id)
        if policy is None:
            raise PolicyNotFoundError(policy_id)
        return policy

    def list_policies(self, enabled_only: bool = True) -> list[Policy]:
        """List all policies.

        Args:
            enabled_only: If True, only return enabled policies.

        Returns:
            List of policies sorted by priority.
        """
        return self._evaluator.list_policies(enabled_only=enabled_only)

    def evaluate(
        self,
        action: str,
        *,
        context: dict[str, Any] | None = None,
        agent: str | None = None,
        risk_score: float | None = None,
    ) -> PolicyResult:
        """Evaluate policies for an action.

        This method checks all applicable policies and returns
        the evaluation result without raising exceptions.

        Args:
            action: The action being performed.
            context: Context data for condition evaluation.
            agent: Optional agent name.
            risk_score: Optional pre-calculated risk score.

        Returns:
            PolicyResult with the evaluation outcome.
        """
        result = self._evaluator.evaluate(
            action,
            context,
            agent=agent,
            risk_score=risk_score,
        )

        # Call audit hooks
        self._call_audit_hooks(action, context, agent, result)

        return result

    def enforce(
        self,
        action: str,
        *,
        context: dict[str, Any] | None = None,
        agent: str | None = None,
        risk_score: float | None = None,
    ) -> PolicyResult:
        """Evaluate and enforce policies for an action.

        This method evaluates policies and raises an exception
        if the action is denied.

        Args:
            action: The action being performed.
            context: Context data for condition evaluation.
            agent: Optional agent name.
            risk_score: Optional pre-calculated risk score.

        Returns:
            PolicyResult if action is allowed.

        Raises:
            PolicyViolationError: If the action is denied.
        """
        result = self.evaluate(
            action,
            context=context,
            agent=agent,
            risk_score=risk_score,
        )

        if not result.allowed:
            raise PolicyViolationError(
                policy_id=result.policy_id or "unknown",
                action=action,
                reason=result.reason,
                agent=agent,
                risk_score=result.risk_score,
            )

        return result

    def can_perform(
        self,
        action: str,
        *,
        context: dict[str, Any] | None = None,
        agent: str | None = None,
    ) -> bool:
        """Check if an action can be performed.

        This is a convenience method that returns a simple boolean.

        Args:
            action: The action to check.
            context: Context data for condition evaluation.
            agent: Optional agent name.

        Returns:
            True if allowed, False if denied.
        """
        result = self.evaluate(action, context=context, agent=agent)
        return result.allowed

    def requires_approval(
        self,
        action: str,
        *,
        context: dict[str, Any] | None = None,
        agent: str | None = None,
    ) -> tuple[bool, list[str]]:
        """Check if an action requires approval.

        Args:
            action: The action to check.
            context: Context data for condition evaluation.
            agent: Optional agent name.

        Returns:
            Tuple of (requires_approval, list_of_approval_roles).
        """
        result = self.evaluate(action, context=context, agent=agent)
        return result.requires_approval, result.approval_roles

    def get_applicable_policies(
        self,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> list[Policy]:
        """Get all policies that apply to an action.

        Args:
            action: The action to check.
            context: Context data for condition evaluation.

        Returns:
            List of applicable policies.
        """
        return self._evaluator.get_applicable_policies(action, context)

    def add_audit_hook(self, hook: callable) -> None:
        """Add an audit hook for policy evaluations.

        Audit hooks are called after every policy evaluation,
        allowing integration with audit logging systems.

        Args:
            hook: Callable with signature:
                  hook(action, context, agent, result) -> None
        """
        self._audit_hooks.append(hook)

    def remove_audit_hook(self, hook: callable) -> bool:
        """Remove an audit hook.

        Args:
            hook: The hook to remove.

        Returns:
            True if removed, False if not found.
        """
        if hook in self._audit_hooks:
            self._audit_hooks.remove(hook)
            return True
        return False

    def _call_audit_hooks(
        self,
        action: str,
        context: dict[str, Any] | None,
        agent: str | None,
        result: PolicyResult,
    ) -> None:
        """Call all registered audit hooks.

        Args:
            action: The action that was evaluated.
            context: Context data.
            agent: Agent name.
            result: Evaluation result.
        """
        for hook in self._audit_hooks:
            try:
                hook(action, context, agent, result)
            except Exception as e:
                # Log hook failures but don't let them affect policy evaluation
                logger.warning(
                    "Audit hook failed: %s (action=%s, agent=%s)",
                    str(e),
                    action,
                    agent,
                    exc_info=True,
                )

    def save_policies(self, path: Path | str) -> None:
        """Save all policies to a YAML file.

        Args:
            path: Path to the output file.
        """
        policies = self.list_policies(enabled_only=False)
        self._loader.save_policies(policies, path)

    def get_statistics(self) -> dict[str, Any]:
        """Get policy engine statistics.

        Returns:
            Dictionary with statistics about loaded policies.
        """
        all_policies = self.list_policies(enabled_only=False)
        enabled_policies = self.list_policies(enabled_only=True)

        by_type: dict[str, int] = {}
        by_risk_level: dict[str, int] = {}

        for policy in all_policies:
            # Count by type
            type_name = policy.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

            # Count by risk level
            risk = policy.risk_level or "unspecified"
            by_risk_level[risk] = by_risk_level.get(risk, 0) + 1

        return {
            "total_policies": len(all_policies),
            "enabled_policies": len(enabled_policies),
            "disabled_policies": len(all_policies) - len(enabled_policies),
            "by_type": by_type,
            "by_risk_level": by_risk_level,
            "audit_hooks": len(self._audit_hooks),
        }
