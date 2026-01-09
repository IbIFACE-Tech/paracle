"""Cost management module for Paracle.

Provides comprehensive cost tracking, budget management, and reporting:
- Token usage tracking
- Cost calculation based on model pricing
- Budget enforcement with alerts
- Cost aggregation and reporting

Usage:
    from paracle_core.cost import CostTracker, CostConfig

    # Initialize tracker with config
    config = CostConfig.from_project_yaml()
    tracker = CostTracker(config)

    # Track usage
    tracker.track_usage(
        model="gpt-4",
        provider="openai",
        prompt_tokens=1000,
        completion_tokens=500,
    )

    # Get cost report
    report = tracker.get_report()
"""

from paracle_core.cost.config import CostConfig
from paracle_core.cost.models import (
    BudgetAlert,
    BudgetStatus,
    CostRecord,
    CostReport,
    CostUsage,
)
from paracle_core.cost.tracker import CostTracker

__all__ = [
    "CostConfig",
    "CostTracker",
    "CostUsage",
    "CostRecord",
    "CostReport",
    "BudgetAlert",
    "BudgetStatus",
]
