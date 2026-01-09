"""Cost and Quality Optimization for Paracle Meta-Agent.

Implements:
- Cost tracking and budget enforcement
- Quality scoring for generated artifacts
- Optimization strategies for provider selection
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from paracle_core.logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class CostConfig(BaseModel):
    """Cost optimization configuration."""

    enabled: bool = True
    max_daily_budget: float = Field(default=10.0, description="Max daily spend in USD")
    max_monthly_budget: float = Field(
        default=100.0, description="Max monthly spend in USD"
    )
    warn_at_percent: int = Field(default=80, description="Warn at this % of budget")
    prefer_cheaper_for_simple: bool = True
    track_costs: bool = True


class CostRecord(BaseModel):
    """Record of a generation cost."""

    generation_id: str
    provider: str
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    timestamp: datetime = Field(default_factory=datetime.now)


class CostReport(BaseModel):
    """Cost report summary."""

    period: str  # "daily", "monthly", "total"
    total_cost: float
    generation_count: int
    avg_cost_per_generation: float
    budget_limit: float | None = None
    budget_remaining: float | None = None
    budget_percent_used: float | None = None
    savings_vs_naive: float = 0.0  # Savings vs always using expensive model
    by_provider: dict[str, float] = Field(default_factory=dict)


class CostOptimizer:
    """Cost optimization engine.

    Tracks costs, enforces budgets, and optimizes provider selection
    based on cost/quality tradeoffs.

    Example:
        >>> optimizer = CostOptimizer()
        >>>
        >>> # Check budget before generation
        >>> if optimizer.can_afford(estimated_cost=0.05):
        ...     result = await generate(...)
        ...     await optimizer.track_cost(result)
        >>>
        >>> # Get cost report
        >>> report = await optimizer.get_report("daily")
        >>> print(f"Daily spend: ${report.total_cost:.2f}")
    """

    # Naive cost baseline (always using most expensive model)
    NAIVE_COST_PER_1K = 0.01  # $0.01 per 1K tokens

    def __init__(
        self,
        enabled: bool = True,
        config: CostConfig | None = None,
        db_path: Path | None = None,
    ):
        """Initialize cost optimizer.

        Args:
            enabled: Enable cost tracking and optimization
            config: Cost configuration
            db_path: Path to cost database
        """
        self.enabled = enabled
        self.config = config or CostConfig()
        self.db_path = db_path or self._default_db_path()

        if enabled:
            self._init_database()
            logger.info(
                "CostOptimizer initialized",
                extra={
                    "daily_budget": self.config.max_daily_budget,
                    "monthly_budget": self.config.max_monthly_budget,
                },
            )

    def select_provider(
        self,
        task_type: str,
        complexity: float,
    ) -> dict[str, Any]:
        """Select optimal provider based on cost/quality tradeoff.

        Args:
            task_type: Type of task
            complexity: Task complexity 0.0-1.0

        Returns:
            Dictionary with provider recommendation
        """
        if not self.enabled:
            return {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "reason": "Cost optimization disabled",
            }

        # Simple tasks → cheap models
        if complexity < 0.3 and self.config.prefer_cheaper_for_simple:
            return {
                "provider": "ollama",
                "model": "llama3.2",
                "reason": "Low complexity task, using local model",
            }

        # Medium complexity → balanced
        if complexity < 0.7:
            return {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "reason": "Medium complexity, using cost-effective model",
            }

        # High complexity → best model
        return {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "reason": "High complexity, using best model",
        }

    def can_afford(self, estimated_cost: float) -> tuple[bool, str]:
        """Check if budget allows for a generation.

        Args:
            estimated_cost: Estimated cost in USD

        Returns:
            Tuple of (can_afford: bool, reason: str)
        """
        if not self.enabled:
            return True, "Cost tracking disabled"

        daily_spent = self._get_period_cost("daily")
        monthly_spent = self._get_period_cost("monthly")

        # Check daily limit
        if daily_spent + estimated_cost > self.config.max_daily_budget:
            return (
                False,
                f"Would exceed daily budget "
                f"(${daily_spent:.2f} + ${estimated_cost:.2f} > "
                f"${self.config.max_daily_budget:.2f})",
            )

        # Check monthly limit
        if monthly_spent + estimated_cost > self.config.max_monthly_budget:
            return (
                False,
                f"Would exceed monthly budget "
                f"(${monthly_spent:.2f} + ${estimated_cost:.2f} > "
                f"${self.config.max_monthly_budget:.2f})",
            )

        return True, "Within budget"

    async def track_cost(self, result: Any) -> None:
        """Track cost of a generation.

        Args:
            result: GenerationResult with cost information
        """
        if not self.enabled or not self.config.track_costs:
            return

        record = CostRecord(
            generation_id=result.id,
            provider=result.provider,
            model=result.model,
            tokens_input=result.tokens_input,
            tokens_output=result.tokens_output,
            cost_usd=result.cost_usd,
        )

        self._save_record(record)
        logger.debug(
            f"Tracked cost: ${record.cost_usd:.4f}",
            extra={"provider": record.provider, "generation_id": record.generation_id},
        )

    async def get_statistics(self) -> dict[str, Any]:
        """Get cost statistics.

        Returns:
            Dictionary with cost statistics
        """
        if not self.enabled:
            return {"enabled": False}

        daily = self._get_period_cost("daily")
        monthly = self._get_period_cost("monthly")
        total = self._get_period_cost("total")

        # Calculate savings vs naive approach
        total_tokens = self._get_total_tokens()
        naive_cost = (total_tokens / 1000) * self.NAIVE_COST_PER_1K
        savings = naive_cost - total if naive_cost > 0 else 0
        savings_percent = (savings / naive_cost * 100) if naive_cost > 0 else 0

        return {
            "daily_cost": round(daily, 4),
            "monthly_cost": round(monthly, 4),
            "total_cost": round(total, 4),
            "daily_budget": self.config.max_daily_budget,
            "monthly_budget": self.config.max_monthly_budget,
            "daily_remaining": round(self.config.max_daily_budget - daily, 4),
            "monthly_remaining": round(self.config.max_monthly_budget - monthly, 4),
            "savings_usd": round(savings, 4),
            "savings_percent": round(savings_percent, 1),
        }

    async def get_report(self, period: str = "daily") -> CostReport:
        """Get detailed cost report.

        Args:
            period: "daily", "monthly", or "total"

        Returns:
            CostReport with detailed breakdown
        """
        if not self.enabled:
            return CostReport(
                period=period,
                total_cost=0,
                generation_count=0,
                avg_cost_per_generation=0,
            )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get time range
        if period == "daily":
            start_time = datetime.now() - timedelta(days=1)
            budget_limit = self.config.max_daily_budget
        elif period == "monthly":
            start_time = datetime.now() - timedelta(days=30)
            budget_limit = self.config.max_monthly_budget
        else:
            start_time = datetime.min
            budget_limit = None

        # Total cost and count
        cursor.execute(
            """
            SELECT SUM(cost_usd), COUNT(*), SUM(tokens_input + tokens_output)
            FROM costs
            WHERE timestamp >= ?
        """,
            (start_time.isoformat(),),
        )
        row = cursor.fetchone()
        total_cost = row[0] or 0
        count = row[1] or 0
        total_tokens = row[2] or 0

        # Cost by provider
        cursor.execute(
            """
            SELECT provider, SUM(cost_usd)
            FROM costs
            WHERE timestamp >= ?
            GROUP BY provider
        """,
            (start_time.isoformat(),),
        )
        by_provider = {row[0]: round(row[1], 4) for row in cursor.fetchall()}

        conn.close()

        # Calculate savings
        naive_cost = (total_tokens / 1000) * self.NAIVE_COST_PER_1K
        savings = naive_cost - total_cost if naive_cost > 0 else 0

        return CostReport(
            period=period,
            total_cost=round(total_cost, 4),
            generation_count=count,
            avg_cost_per_generation=round(total_cost / count, 4) if count > 0 else 0,
            budget_limit=budget_limit,
            budget_remaining=(
                round(budget_limit - total_cost, 4) if budget_limit else None
            ),
            budget_percent_used=(
                round(total_cost / budget_limit * 100, 1) if budget_limit else None
            ),
            savings_vs_naive=round(savings, 4),
            by_provider=by_provider,
        )

    def _get_period_cost(self, period: str) -> float:
        """Get total cost for a period."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if period == "daily":
            start_time = datetime.now() - timedelta(days=1)
        elif period == "monthly":
            start_time = datetime.now() - timedelta(days=30)
        else:
            start_time = datetime.min

        cursor.execute(
            """
            SELECT SUM(cost_usd) FROM costs WHERE timestamp >= ?
        """,
            (start_time.isoformat(),),
        )
        result = cursor.fetchone()[0] or 0
        conn.close()
        return result

    def _get_total_tokens(self) -> int:
        """Get total tokens used."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(tokens_input + tokens_output) FROM costs")
        result = cursor.fetchone()[0] or 0
        conn.close()
        return result

    def _save_record(self, record: CostRecord) -> None:
        """Save cost record to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO costs (
                generation_id, provider, model,
                tokens_input, tokens_output, cost_usd, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.generation_id,
                record.provider,
                record.model,
                record.tokens_input,
                record.tokens_output,
                record.cost_usd,
                record.timestamp.isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def _init_database(self) -> None:
        """Initialize cost database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                tokens_input INTEGER NOT NULL,
                tokens_output INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_costs_timestamp
            ON costs(timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_costs_provider
            ON costs(provider)
        """
        )

        conn.commit()
        conn.close()

    def _default_db_path(self) -> Path:
        """Get default database path."""
        return Path.cwd() / ".parac" / "memory" / "data" / "meta_costs.db"


class QualityScorer:
    """Scores quality of generated artifacts.

    Evaluates:
    - Structural completeness
    - Adherence to Paracle conventions
    - Content quality indicators
    """

    # Quality criteria weights
    WEIGHTS = {
        "completeness": 0.3,
        "conventions": 0.25,
        "clarity": 0.2,
        "specificity": 0.15,
        "feasibility": 0.1,
    }

    def __init__(self):
        """Initialize quality scorer."""
        logger.debug("QualityScorer initialized")

    async def score(self, result: Any) -> float:
        """Score a generation result.

        Args:
            result: GenerationResult to score

        Returns:
            Quality score 0-10
        """
        content = result.content

        scores = {
            "completeness": self._score_completeness(content, result.artifact_type),
            "conventions": self._score_conventions(content, result.artifact_type),
            "clarity": self._score_clarity(content),
            "specificity": self._score_specificity(content),
            "feasibility": self._score_feasibility(content, result.artifact_type),
        }

        # Weighted average
        total = sum(scores[k] * self.WEIGHTS[k] for k in scores)

        logger.debug(
            f"Quality score: {total:.1f}",
            extra={"breakdown": scores, "artifact_type": result.artifact_type},
        )

        return round(total, 1)

    def _score_completeness(self, content: str, artifact_type: str) -> float:
        """Score structural completeness."""
        score = 5.0  # Base score

        if artifact_type == "agent":
            # Check for required sections
            required = ["name", "role", "capabilities", "system_prompt"]
            for req in required:
                if req.lower() in content.lower():
                    score += 1.25
        elif artifact_type == "workflow":
            required = ["name", "steps", "inputs", "outputs"]
            for req in required:
                if req.lower() in content.lower():
                    score += 1.25
        elif artifact_type == "skill":
            required = ["name", "description", "examples"]
            for req in required:
                if req.lower() in content.lower():
                    score += 1.67
        elif artifact_type == "policy":
            required = ["name", "rules", "enforcement"]
            for req in required:
                if req.lower() in content.lower():
                    score += 1.67

        return min(10.0, score)

    def _score_conventions(self, content: str, artifact_type: str) -> float:
        """Score adherence to Paracle conventions."""
        score = 5.0

        # Check for YAML structure indicators
        if "---" in content or ": " in content:
            score += 1.0

        # Check for proper markdown headers
        if "#" in content:
            score += 1.0

        # Check for code blocks if applicable
        if "```" in content:
            score += 1.0

        # Check length (not too short, not excessive)
        length = len(content)
        if 200 < length < 5000:
            score += 2.0
        elif length < 200:
            score -= 2.0

        return max(0.0, min(10.0, score))

    def _score_clarity(self, content: str) -> float:
        """Score content clarity."""
        score = 5.0

        # Check for bullet points / lists
        if "- " in content or "* " in content:
            score += 1.5

        # Check for proper paragraphs
        paragraphs = content.split("\n\n")
        if 2 <= len(paragraphs) <= 20:
            score += 1.5

        # Check for examples
        if "example" in content.lower() or "```" in content:
            score += 2.0

        return min(10.0, score)

    def _score_specificity(self, content: str) -> float:
        """Score content specificity."""
        score = 5.0

        # Check for specific tool/skill references
        specific_terms = [
            "paracle",
            "agent",
            "workflow",
            "skill",
            "tool",
            "policy",
            "yaml",
            "api",
        ]
        matches = sum(1 for term in specific_terms if term in content.lower())
        score += min(matches * 0.5, 3.0)

        # Check for concrete examples/values
        if any(char in content for char in ['"', "'", ":"]):  # Likely has values
            score += 2.0

        return min(10.0, score)

    def _score_feasibility(self, content: str, artifact_type: str) -> float:
        """Score implementation feasibility."""
        score = 7.0  # Start high, deduct for issues

        # Check for overly complex patterns
        if content.count("{") > 20 or content.count("(") > 30:
            score -= 2.0

        # Check for reasonable length
        if len(content) > 10000:
            score -= 1.0

        # Check for TODO/FIXME indicating incomplete
        if "TODO" in content or "FIXME" in content:
            score -= 2.0

        return max(0.0, min(10.0, score))


__all__ = [
    "CostConfig",
    "CostRecord",
    "CostReport",
    "CostOptimizer",
    "QualityScorer",
]
