"""Paracle Governance Package.

This package provides governance layer functionality for ISO 42001 compliance:
- Policy Engine: Define and evaluate governance policies
- Risk Scoring: Calculate risk scores for agent actions
- Approval Workflows: Multi-level approval management
- Compliance: Policy enforcement and audit integration

Example:
    >>> from paracle_governance import PolicyEngine, RiskScorer
    >>> engine = PolicyEngine()
    >>> engine.load_policies("policies.yaml")
    >>> result = engine.evaluate(action="write_file", agent="coder", context={})
    >>> print(result.allowed)  # True or False
"""

from .engine import PolicyEngine
from .evaluator import PolicyEvaluator
from .exceptions import (
    GovernanceError,
    PolicyEvaluationError,
    PolicyNotFoundError,
    PolicyViolationError,
    RiskThresholdExceededError,
)
from .loader import PolicyLoader
from .policies import (
    Policy,
    PolicyAction,
    PolicyCondition,
    PolicyResult,
    PolicyType,
    RegexTimeoutError,
    safe_regex_match,
    validate_regex_pattern,
)
from .risk.factors import RiskFactor, RiskLevel
from .risk.scorer import RiskScorer
from .risk.thresholds import RiskThresholds

__all__ = [
    # Policy classes
    "Policy",
    "PolicyAction",
    "PolicyCondition",
    "PolicyResult",
    "PolicyType",
    # Regex safety
    "RegexTimeoutError",
    "validate_regex_pattern",
    "safe_regex_match",
    # Engine and evaluation
    "PolicyEngine",
    "PolicyEvaluator",
    "PolicyLoader",
    # Risk scoring
    "RiskScorer",
    "RiskFactor",
    "RiskLevel",
    "RiskThresholds",
    # Exceptions
    "GovernanceError",
    "PolicyNotFoundError",
    "PolicyViolationError",
    "PolicyEvaluationError",
    "RiskThresholdExceededError",
]

__version__ = "1.0.1"
