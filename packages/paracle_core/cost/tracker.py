"""Cost tracking and budget management.

Central service for tracking all LLM costs, enforcing budgets,
and generating alerts.
"""

import json
import logging
import sqlite3
from collections import defaultdict
from pathlib import Path
from threading import Lock
from typing import Any

from paracle_core.compat import UTC, datetime, timedelta
from paracle_core.cost.config import CostConfig
from paracle_core.cost.models import (
    BudgetAlert,
    BudgetStatus,
    CostRecord,
    CostReport,
    CostUsage,
)

logger = logging.getLogger("paracle.cost")


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded and blocking is enabled."""

    def __init__(
        self,
        budget_type: str,
        limit: float,
        current: float,
        message: str | None = None,
    ):
        self.budget_type = budget_type
        self.limit = limit
        self.current = current
        super().__init__(
            message
            or f"Budget exceeded: {budget_type} limit ${limit:.2f}, current ${current:.2f}"
        )


class CostTracker:
    """Tracks LLM costs, enforces budgets, and generates reports.

    The tracker:
    - Calculates costs based on token usage and model pricing
    - Persists cost records to SQLite database
    - Enforces budget limits with configurable actions
    - Generates alerts when thresholds are crossed
    - Provides aggregated reports and statistics

    Example:
        >>> config = CostConfig.from_project_yaml()
        >>> tracker = CostTracker(config)
        >>> tracker.track_usage(
        ...     model="gpt-4",
        ...     provider="openai",
        ...     prompt_tokens=1000,
        ...     completion_tokens=500,
        ... )
        >>> report = tracker.get_report()
        >>> print(f"Total cost: ${report.total_usage.total_cost:.4f}")
    """

    def __init__(
        self,
        config: CostConfig | None = None,
        db_path: Path | str | None = None,
    ):
        """Initialize the cost tracker.

        Args:
            config: Cost configuration (loaded from project.yaml if None)
            db_path: Override path to cost database
        """
        self.config = config or CostConfig.from_project_yaml()

        # Determine database path
        if db_path:
            self._db_path = Path(db_path)
        elif self.config.tracking.db_path:
            self._db_path = Path(self.config.tracking.db_path)
        else:
            self._db_path = self._find_default_db_path()

        # In-memory cache for current session
        self._session_records: list[CostRecord] = []
        self._session_usage = CostUsage()

        # Alert tracking
        self._last_alerts: dict[str, datetime] = {}
        self._pending_alerts: list[BudgetAlert] = []

        # Thread safety
        self._lock = Lock()

        # Initialize database
        if self.config.tracking.enabled and self.config.tracking.persist_to_db:
            self._init_database()

    def _find_default_db_path(self) -> Path:
        """Find default database path in .parac/memory/data/ directory."""
        current = Path.cwd()
        for parent in [current, *current.parents]:
            parac_dir = parent / ".parac"
            if parac_dir.is_dir():
                return parac_dir / "memory" / "data" / "costs.db"
        return Path.cwd() / ".parac" / "memory" / "data" / "costs.db"

    def _init_database(self) -> None:
        """Initialize SQLite database for cost persistence."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        # Create cost_records table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cost_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                prompt_cost REAL NOT NULL,
                completion_cost REAL NOT NULL,
                total_cost REAL NOT NULL,
                execution_id TEXT,
                workflow_id TEXT,
                step_id TEXT,
                agent_id TEXT,
                metadata_json TEXT
            )
        """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cost_timestamp ON cost_records(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cost_provider ON cost_records(provider)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cost_model ON cost_records(model)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cost_workflow ON cost_records(workflow_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cost_execution ON cost_records(execution_id)"
        )

        # Create budget_alerts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS budget_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                budget_type TEXT NOT NULL,
                budget_limit REAL NOT NULL,
                current_usage REAL NOT NULL,
                usage_percent REAL NOT NULL,
                message TEXT NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()

    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> tuple[float, float, float]:
        """Calculate cost for token usage.

        Args:
            provider: Provider name (e.g., "openai")
            model: Model name (e.g., "gpt-4")
            prompt_tokens: Number of prompt/input tokens
            completion_tokens: Number of completion/output tokens

        Returns:
            Tuple of (prompt_cost, completion_cost, total_cost) in USD
        """
        # Try to get pricing from config
        pricing = self.config.get_model_pricing(provider, model)

        if pricing:
            input_rate, output_rate = pricing
        else:
            # Default fallback pricing
            logger.warning(f"No pricing found for {provider}/{model}, using defaults")
            input_rate = 1.0  # $1 per million tokens
            output_rate = 2.0  # $2 per million tokens

        # Calculate costs (rates are per million tokens)
        prompt_cost = (prompt_tokens / 1_000_000) * input_rate
        completion_cost = (completion_tokens / 1_000_000) * output_rate
        total_cost = prompt_cost + completion_cost

        return (prompt_cost, completion_cost, total_cost)

    def track_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        execution_id: str | None = None,
        workflow_id: str | None = None,
        step_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CostRecord:
        """Track token usage and calculate cost.

        Args:
            provider: Provider name (e.g., "openai")
            model: Model name (e.g., "gpt-4")
            prompt_tokens: Number of prompt/input tokens
            completion_tokens: Number of completion/output tokens
            execution_id: Optional execution ID for correlation
            workflow_id: Optional workflow ID
            step_id: Optional step ID
            agent_id: Optional agent ID
            metadata: Optional additional metadata

        Returns:
            CostRecord with calculated costs

        Raises:
            BudgetExceededError: If budget exceeded and blocking enabled
        """
        if not self.config.tracking.enabled:
            # Return zero-cost record if tracking disabled
            return CostRecord(
                timestamp=_utcnow(),
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                prompt_cost=0.0,
                completion_cost=0.0,
                total_cost=0.0,
            )

        # Calculate costs
        prompt_cost, completion_cost, total_cost = self.calculate_cost(
            provider, model, prompt_tokens, completion_tokens
        )

        # Create record
        record = CostRecord(
            timestamp=_utcnow(),
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
            execution_id=execution_id,
            workflow_id=workflow_id,
            step_id=step_id,
            agent_id=agent_id,
            metadata=metadata or {},
        )

        with self._lock:
            # Check budget before adding
            if self.config.budget.enabled:
                self._check_budget(record, workflow_id)

            # Add to session
            self._session_records.append(record)
            self._session_usage.add(record)

            # Persist to database
            if self.config.tracking.persist_to_db:
                self._persist_record(record)

        logger.debug(
            f"Tracked cost: {provider}/{model} - "
            f"{prompt_tokens}+{completion_tokens} tokens = ${total_cost:.6f}"
        )

        return record

    def _check_budget(
        self,
        record: CostRecord,
        workflow_id: str | None = None,
    ) -> None:
        """Check budget limits and raise alerts.

        Args:
            record: Cost record to check against budgets
            workflow_id: Optional workflow ID for per-workflow budget

        Raises:
            BudgetExceededError: If budget exceeded and blocking enabled
        """
        budget = self.config.budget

        # Check daily budget
        if budget.daily_limit is not None:
            daily_usage = self.get_daily_usage()
            new_total = daily_usage.total_cost + record.total_cost

            self._check_limit(
                "daily",
                budget.daily_limit,
                new_total,
                budget.warning_threshold,
                budget.critical_threshold,
                budget.block_on_exceed,
            )

        # Check monthly budget
        if budget.monthly_limit is not None:
            monthly_usage = self.get_monthly_usage()
            new_total = monthly_usage.total_cost + record.total_cost

            self._check_limit(
                "monthly",
                budget.monthly_limit,
                new_total,
                budget.warning_threshold,
                budget.critical_threshold,
                budget.block_on_exceed,
            )

        # Check per-workflow budget
        if budget.workflow_limit is not None and workflow_id:
            workflow_usage = self.get_workflow_usage(workflow_id)
            new_total = workflow_usage.total_cost + record.total_cost

            self._check_limit(
                f"workflow:{workflow_id}",
                budget.workflow_limit,
                new_total,
                budget.warning_threshold,
                budget.critical_threshold,
                budget.block_on_exceed,
            )

        # Check total budget
        if budget.total_limit is not None:
            total_usage = self.get_total_usage()
            new_total = total_usage.total_cost + record.total_cost

            self._check_limit(
                "total",
                budget.total_limit,
                new_total,
                budget.warning_threshold,
                budget.critical_threshold,
                budget.block_on_exceed,
            )

    def _check_limit(
        self,
        budget_type: str,
        limit: float,
        current: float,
        warning_threshold: float,
        critical_threshold: float,
        block_on_exceed: bool,
    ) -> None:
        """Check a specific budget limit.

        Args:
            budget_type: Type of budget (daily, monthly, workflow, total)
            limit: Budget limit in USD
            current: Current usage in USD
            warning_threshold: Warning threshold (0.0-1.0)
            critical_threshold: Critical threshold (0.0-1.0)
            block_on_exceed: Whether to block when exceeded
        """
        usage_percent = current / limit if limit > 0 else 0.0

        # Determine status
        if usage_percent >= 1.0:
            status = BudgetStatus.EXCEEDED
        elif usage_percent >= critical_threshold:
            status = BudgetStatus.CRITICAL
        elif usage_percent >= warning_threshold:
            status = BudgetStatus.WARNING
        else:
            status = BudgetStatus.OK

        # Create alert if needed
        if status != BudgetStatus.OK:
            self._create_alert(budget_type, limit, current, usage_percent, status)

        # Block if exceeded and blocking enabled
        if status == BudgetStatus.EXCEEDED and block_on_exceed:
            raise BudgetExceededError(budget_type, limit, current)

    def _create_alert(
        self,
        budget_type: str,
        limit: float,
        current: float,
        usage_percent: float,
        status: BudgetStatus,
    ) -> None:
        """Create a budget alert.

        Respects minimum interval between alerts of same type.
        """
        # Check if we should suppress this alert
        min_interval = timedelta(minutes=self.config.alerts.min_interval_minutes)
        last_alert_time = self._last_alerts.get(budget_type)

        if last_alert_time and (_utcnow() - last_alert_time) < min_interval:
            return  # Suppress alert

        # Create alert
        message = (
            f"Budget {status.value}: {budget_type} at {usage_percent:.1%} "
            f"(${current:.2f} / ${limit:.2f})"
        )

        alert = BudgetAlert(
            timestamp=_utcnow(),
            status=status,
            budget_type=budget_type,
            budget_limit=limit,
            current_usage=current,
            usage_percent=usage_percent,
            message=message,
        )

        self._last_alerts[budget_type] = alert.timestamp
        self._pending_alerts.append(alert)

        # Log alert
        if self.config.alerts.log_alerts:
            if status == BudgetStatus.EXCEEDED:
                logger.error(message)
            elif status == BudgetStatus.CRITICAL:
                logger.warning(message)
            else:
                logger.info(message)

        # Persist alert
        if self.config.tracking.persist_to_db:
            self._persist_alert(alert)

    def _persist_record(self, record: CostRecord) -> None:
        """Persist cost record to database."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO cost_records (
                timestamp, provider, model,
                prompt_tokens, completion_tokens, total_tokens,
                prompt_cost, completion_cost, total_cost,
                execution_id, workflow_id, step_id, agent_id,
                metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.timestamp.isoformat(),
                record.provider,
                record.model,
                record.prompt_tokens,
                record.completion_tokens,
                record.total_tokens,
                record.prompt_cost,
                record.completion_cost,
                record.total_cost,
                record.execution_id,
                record.workflow_id,
                record.step_id,
                record.agent_id,
                json.dumps(record.metadata) if record.metadata else None,
            ),
        )

        conn.commit()
        conn.close()

    def _persist_alert(self, alert: BudgetAlert) -> None:
        """Persist budget alert to database."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO budget_alerts (
                timestamp, status, budget_type,
                budget_limit, current_usage, usage_percent, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                alert.timestamp.isoformat(),
                alert.status.value,
                alert.budget_type,
                alert.budget_limit,
                alert.current_usage,
                alert.usage_percent,
                alert.message,
            ),
        )

        conn.commit()
        conn.close()

    # ========================================
    # Usage Queries
    # ========================================

    def get_session_usage(self) -> CostUsage:
        """Get usage for current session."""
        return self._session_usage

    def get_daily_usage(self, date: datetime | None = None) -> CostUsage:
        """Get usage for a specific day.

        Args:
            date: Date to query (default: today)

        Returns:
            CostUsage for the day
        """
        if date is None:
            date = _utcnow()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        return self._query_usage(start, end)

    def get_monthly_usage(
        self, year: int | None = None, month: int | None = None
    ) -> CostUsage:
        """Get usage for a specific month.

        Args:
            year: Year (default: current year)
            month: Month (default: current month)

        Returns:
            CostUsage for the month
        """
        now = _utcnow()
        year = year or now.year
        month = month or now.month

        start = datetime(year, month, 1, tzinfo=UTC)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=UTC)
        else:
            end = datetime(year, month + 1, 1, tzinfo=UTC)

        return self._query_usage(start, end)

    def get_workflow_usage(self, workflow_id: str) -> CostUsage:
        """Get usage for a specific workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            CostUsage for the workflow
        """
        return self._query_usage(workflow_id=workflow_id)

    def get_total_usage(self) -> CostUsage:
        """Get total usage across all time."""
        return self._query_usage()

    def _query_usage(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        workflow_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> CostUsage:
        """Query usage from database with filters.

        Args:
            start: Start timestamp
            end: End timestamp
            workflow_id: Filter by workflow ID
            provider: Filter by provider
            model: Filter by model

        Returns:
            Aggregated CostUsage
        """
        usage = CostUsage()

        if not self.config.tracking.persist_to_db or not self._db_path.exists():
            # Return session data only
            for record in self._session_records:
                if start and record.timestamp < start:
                    continue
                if end and record.timestamp >= end:
                    continue
                if workflow_id and record.workflow_id != workflow_id:
                    continue
                if provider and record.provider != provider:
                    continue
                if model and record.model != model:
                    continue
                usage.add(record)
            return usage

        # Query database
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if start:
            where_clauses.append("timestamp >= ?")
            params.append(start.isoformat())

        if end:
            where_clauses.append("timestamp < ?")
            params.append(end.isoformat())

        if workflow_id:
            where_clauses.append("workflow_id = ?")
            params.append(workflow_id)

        if provider:
            where_clauses.append("provider = ?")
            params.append(provider)

        if model:
            where_clauses.append("model = ?")
            params.append(model)

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        cursor.execute(
            f"""
            SELECT
                SUM(prompt_tokens),
                SUM(completion_tokens),
                SUM(total_tokens),
                SUM(prompt_cost),
                SUM(completion_cost),
                SUM(total_cost),
                COUNT(*),
                MIN(timestamp),
                MAX(timestamp)
            FROM cost_records
            WHERE {where_clause}
        """,
            params,
        )

        row = cursor.fetchone()
        conn.close()

        if row and row[0] is not None:
            usage.prompt_tokens = row[0] or 0
            usage.completion_tokens = row[1] or 0
            usage.total_tokens = row[2] or 0
            usage.prompt_cost = row[3] or 0.0
            usage.completion_cost = row[4] or 0.0
            usage.total_cost = row[5] or 0.0
            usage.request_count = row[6] or 0
            if row[7]:
                usage.period_start = datetime.fromisoformat(row[7])
            if row[8]:
                usage.period_end = datetime.fromisoformat(row[8])

        return usage

    # ========================================
    # Reports
    # ========================================

    def get_report(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> CostReport:
        """Generate comprehensive cost report.

        Args:
            start: Report start time
            end: Report end time

        Returns:
            CostReport with breakdowns
        """
        report = CostReport(
            period_start=start,
            period_end=end or _utcnow(),
        )

        # Get total usage
        report.total_usage = self._query_usage(start, end)

        # Get breakdowns
        if self.config.tracking.persist_to_db and self._db_path.exists():
            report.by_provider = self._get_usage_by_field("provider", start, end)
            report.by_model = self._get_usage_by_field("model", start, end)
            report.by_workflow = self._get_usage_by_field("workflow_id", start, end)
            report.by_agent = self._get_usage_by_field("agent_id", start, end)

            # Get top consumers
            report.top_models = sorted(
                [(k, v.total_cost) for k, v in report.by_model.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10]

            report.top_workflows = sorted(
                [(k, v.total_cost) for k, v in report.by_workflow.items() if k],
                key=lambda x: x[1],
                reverse=True,
            )[:10]

        # Get budget status
        report.budget_status = self._get_current_budget_status()
        report.budget_alerts = [a.to_dict() for a in self._pending_alerts]

        return report

    def _get_usage_by_field(
        self,
        field: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[str, CostUsage]:
        """Get usage grouped by a field."""
        result: dict[str, CostUsage] = defaultdict(CostUsage)

        if not self._db_path.exists():
            return dict(result)

        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        where_clauses = [f"{field} IS NOT NULL"]
        params = []

        if start:
            where_clauses.append("timestamp >= ?")
            params.append(start.isoformat())

        if end:
            where_clauses.append("timestamp < ?")
            params.append(end.isoformat())

        where_clause = " AND ".join(where_clauses)

        cursor.execute(
            f"""
            SELECT
                {field},
                SUM(prompt_tokens),
                SUM(completion_tokens),
                SUM(total_tokens),
                SUM(prompt_cost),
                SUM(completion_cost),
                SUM(total_cost),
                COUNT(*)
            FROM cost_records
            WHERE {where_clause}
            GROUP BY {field}
        """,
            params,
        )

        for row in cursor.fetchall():
            key = row[0]
            usage = CostUsage(
                prompt_tokens=row[1] or 0,
                completion_tokens=row[2] or 0,
                total_tokens=row[3] or 0,
                prompt_cost=row[4] or 0.0,
                completion_cost=row[5] or 0.0,
                total_cost=row[6] or 0.0,
                request_count=row[7] or 0,
            )
            result[key] = usage

        conn.close()
        return dict(result)

    def _get_current_budget_status(self) -> BudgetStatus:
        """Get current overall budget status."""
        if not self.config.budget.enabled:
            return BudgetStatus.OK

        statuses = []

        if self.config.budget.daily_limit:
            daily = self.get_daily_usage()
            percent = daily.total_cost / self.config.budget.daily_limit
            if percent >= 1.0:
                statuses.append(BudgetStatus.EXCEEDED)
            elif percent >= self.config.budget.critical_threshold:
                statuses.append(BudgetStatus.CRITICAL)
            elif percent >= self.config.budget.warning_threshold:
                statuses.append(BudgetStatus.WARNING)

        if self.config.budget.monthly_limit:
            monthly = self.get_monthly_usage()
            percent = monthly.total_cost / self.config.budget.monthly_limit
            if percent >= 1.0:
                statuses.append(BudgetStatus.EXCEEDED)
            elif percent >= self.config.budget.critical_threshold:
                statuses.append(BudgetStatus.CRITICAL)
            elif percent >= self.config.budget.warning_threshold:
                statuses.append(BudgetStatus.WARNING)

        # Return worst status
        if BudgetStatus.EXCEEDED in statuses:
            return BudgetStatus.EXCEEDED
        if BudgetStatus.CRITICAL in statuses:
            return BudgetStatus.CRITICAL
        if BudgetStatus.WARNING in statuses:
            return BudgetStatus.WARNING
        return BudgetStatus.OK

    def get_pending_alerts(self) -> list[BudgetAlert]:
        """Get pending budget alerts."""
        alerts = self._pending_alerts.copy()
        return alerts

    def clear_pending_alerts(self) -> None:
        """Clear pending alerts after they've been handled."""
        self._pending_alerts.clear()

    # ========================================
    # Estimation
    # ========================================

    def estimate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        estimated_completion_tokens: int,
    ) -> float:
        """Estimate cost before execution.

        Args:
            provider: Provider name
            model: Model name
            prompt_tokens: Input token count
            estimated_completion_tokens: Estimated output tokens

        Returns:
            Estimated total cost in USD
        """
        _, _, total = self.calculate_cost(
            provider, model, prompt_tokens, estimated_completion_tokens
        )
        return total

    def would_exceed_budget(
        self,
        estimated_cost: float,
        workflow_id: str | None = None,
    ) -> tuple[bool, str | None]:
        """Check if an estimated cost would exceed any budget.

        Args:
            estimated_cost: Estimated cost of operation
            workflow_id: Optional workflow ID

        Returns:
            Tuple of (would_exceed, budget_type) where budget_type
            indicates which budget would be exceeded
        """
        if not self.config.budget.enabled:
            return (False, None)

        # Check daily
        if self.config.budget.daily_limit:
            daily = self.get_daily_usage()
            if daily.total_cost + estimated_cost > self.config.budget.daily_limit:
                return (True, "daily")

        # Check monthly
        if self.config.budget.monthly_limit:
            monthly = self.get_monthly_usage()
            if monthly.total_cost + estimated_cost > self.config.budget.monthly_limit:
                return (True, "monthly")

        # Check workflow
        if self.config.budget.workflow_limit and workflow_id:
            workflow = self.get_workflow_usage(workflow_id)
            if workflow.total_cost + estimated_cost > self.config.budget.workflow_limit:
                return (True, f"workflow:{workflow_id}")

        # Check total
        if self.config.budget.total_limit:
            total = self.get_total_usage()
            if total.total_cost + estimated_cost > self.config.budget.total_limit:
                return (True, "total")

        return (False, None)

    # ========================================
    # Maintenance
    # ========================================

    def cleanup_old_records(self, dry_run: bool = True) -> int:
        """Clean up old cost records based on retention policy.

        Args:
            dry_run: If True, only count what would be deleted

        Returns:
            Number of records deleted (or would be deleted)
        """
        if not self._db_path.exists():
            return 0

        cutoff = _utcnow() - timedelta(days=self.config.tracking.retention_days)

        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        # Count records to delete
        cursor.execute(
            "SELECT COUNT(*) FROM cost_records WHERE timestamp < ?",
            (cutoff.isoformat(),),
        )
        count = cursor.fetchone()[0]

        if not dry_run and count > 0:
            cursor.execute(
                "DELETE FROM cost_records WHERE timestamp < ?",
                (cutoff.isoformat(),),
            )
            conn.commit()

        conn.close()
        return count


# Global tracker instance
_global_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = CostTracker()
    return _global_tracker


def reset_cost_tracker() -> None:
    """Reset the global cost tracker (for testing)."""
    global _global_tracker
    _global_tracker = None
