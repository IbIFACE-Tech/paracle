"""Cost management data models.

Defines all models for tracking, aggregating, and reporting costs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from paracle_core.compat import UTC, datetime


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class BudgetStatus(str, Enum):
    """Budget status levels."""

    OK = "ok"  # Under threshold
    WARNING = "warning"  # Above warning threshold
    CRITICAL = "critical"  # Above critical threshold
    EXCEEDED = "exceeded"  # Budget exceeded


@dataclass
class CostRecord:
    """Record of a single cost event."""

    timestamp: datetime
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost: float
    completion_cost: float
    total_cost: float
    execution_id: str | None = None
    workflow_id: str | None = None
    step_id: str | None = None
    agent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_cost": self.prompt_cost,
            "completion_cost": self.completion_cost,
            "total_cost": self.total_cost,
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "metadata": self.metadata,
        }


class CostUsage(BaseModel):
    """Aggregated cost usage for a period or context."""

    # Token counts
    prompt_tokens: int = Field(default=0, ge=0, description="Total prompt tokens")
    completion_tokens: int = Field(
        default=0, ge=0, description="Total completion tokens"
    )
    total_tokens: int = Field(default=0, ge=0, description="Total tokens")

    # Costs in USD
    prompt_cost: float = Field(default=0.0, ge=0.0, description="Total prompt cost")
    completion_cost: float = Field(
        default=0.0, ge=0.0, description="Total completion cost"
    )
    total_cost: float = Field(default=0.0, ge=0.0, description="Total cost")

    # Counts
    request_count: int = Field(default=0, ge=0, description="Number of requests")

    # Period
    period_start: datetime | None = Field(default=None, description="Period start")
    period_end: datetime | None = Field(default=None, description="Period end")

    def add(self, record: CostRecord) -> None:
        """Add a cost record to this usage."""
        self.prompt_tokens += record.prompt_tokens
        self.completion_tokens += record.completion_tokens
        self.total_tokens += record.total_tokens
        self.prompt_cost += record.prompt_cost
        self.completion_cost += record.completion_cost
        self.total_cost += record.total_cost
        self.request_count += 1

        # Update period bounds
        if self.period_start is None or record.timestamp < self.period_start:
            self.period_start = record.timestamp
        if self.period_end is None or record.timestamp > self.period_end:
            self.period_end = record.timestamp

    def merge(self, other: "CostUsage") -> "CostUsage":
        """Merge another usage into a new CostUsage instance."""
        merged = CostUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            prompt_cost=self.prompt_cost + other.prompt_cost,
            completion_cost=self.completion_cost + other.completion_cost,
            total_cost=self.total_cost + other.total_cost,
            request_count=self.request_count + other.request_count,
        )

        # Merge period bounds
        starts = [s for s in [self.period_start, other.period_start] if s is not None]
        ends = [e for e in [self.period_end, other.period_end] if e is not None]

        if starts:
            merged.period_start = min(starts)
        if ends:
            merged.period_end = max(ends)

        return merged


@dataclass
class BudgetAlert:
    """Budget alert notification."""

    timestamp: datetime
    status: BudgetStatus
    budget_type: str  # "daily", "monthly", "workflow", "total"
    budget_limit: float
    current_usage: float
    usage_percent: float
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "budget_type": self.budget_type,
            "budget_limit": self.budget_limit,
            "current_usage": self.current_usage,
            "usage_percent": self.usage_percent,
            "message": self.message,
        }


class CostReport(BaseModel):
    """Comprehensive cost report."""

    generated_at: datetime = Field(default_factory=_utcnow)
    period_start: datetime | None = None
    period_end: datetime | None = None

    # Summary
    total_usage: CostUsage = Field(default_factory=CostUsage)

    # Breakdown by provider
    by_provider: dict[str, CostUsage] = Field(default_factory=dict)

    # Breakdown by model
    by_model: dict[str, CostUsage] = Field(default_factory=dict)

    # Breakdown by workflow
    by_workflow: dict[str, CostUsage] = Field(default_factory=dict)

    # Breakdown by agent
    by_agent: dict[str, CostUsage] = Field(default_factory=dict)

    # Budget status
    budget_status: BudgetStatus = Field(default=BudgetStatus.OK)
    budget_alerts: list[dict[str, Any]] = Field(default_factory=list)

    # Top consumers
    top_models: list[tuple[str, float]] = Field(default_factory=list)
    top_workflows: list[tuple[str, float]] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "period_start": (
                self.period_start.isoformat() if self.period_start else None
            ),
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "summary": {
                "total_cost": self.total_usage.total_cost,
                "total_tokens": self.total_usage.total_tokens,
                "request_count": self.total_usage.request_count,
                "prompt_cost": self.total_usage.prompt_cost,
                "completion_cost": self.total_usage.completion_cost,
            },
            "by_provider": {k: v.model_dump() for k, v in self.by_provider.items()},
            "by_model": {k: v.model_dump() for k, v in self.by_model.items()},
            "by_workflow": {k: v.model_dump() for k, v in self.by_workflow.items()},
            "by_agent": {k: v.model_dump() for k, v in self.by_agent.items()},
            "budget": {
                "status": self.budget_status.value,
                "alerts": self.budget_alerts,
            },
            "top_consumers": {
                "models": [{"model": m, "cost": c} for m, c in self.top_models],
                "workflows": [
                    {"workflow": w, "cost": c} for w, c in self.top_workflows
                ],
            },
        }
