"""Unit tests for cost management module."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from paracle_core.cost.config import BudgetConfig, CostConfig, TrackingConfig
from paracle_core.cost.models import (
    BudgetAlert,
    BudgetStatus,
    CostRecord,
    CostReport,
    CostUsage,
)
from paracle_core.cost.tracker import BudgetExceededError, CostTracker


class TestCostConfig:
    """Tests for CostConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CostConfig()

        assert config.tracking.enabled is True
        assert config.tracking.persist_to_db is True
        assert config.tracking.retention_days == 90

        assert config.budget.enabled is False
        assert config.budget.daily_limit is None
        assert config.budget.warning_threshold == 0.8
        assert config.budget.critical_threshold == 0.95

        assert config.alerts.enabled is True
        assert config.currency == "USD"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "tracking": {"enabled": True, "retention_days": 30},
            "budget": {"enabled": True, "daily_limit": 10.0},
        }

        config = CostConfig.from_dict(data)

        assert config.tracking.enabled is True
        assert config.tracking.retention_days == 30
        assert config.budget.enabled is True
        assert config.budget.daily_limit == 10.0

    def test_get_model_pricing_exact_match(self):
        """Test getting pricing for exact model match."""
        config = CostConfig()

        pricing = config.get_model_pricing("openai", "gpt-4")
        assert pricing is not None
        assert pricing == (30.0, 60.0)

    def test_get_model_pricing_prefix_match(self):
        """Test getting pricing for model prefix match."""
        config = CostConfig()

        pricing = config.get_model_pricing("openai", "gpt-4-0125-preview")
        assert pricing is not None
        assert pricing[0] == 30.0  # Falls back to gpt-4

    def test_get_model_pricing_not_found(self):
        """Test getting pricing for unknown model."""
        config = CostConfig()

        pricing = config.get_model_pricing("unknown", "unknown-model")
        assert pricing is None


class TestCostUsage:
    """Tests for CostUsage model."""

    def test_default_values(self):
        """Test default usage values."""
        usage = CostUsage()

        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
        assert usage.total_cost == 0.0
        assert usage.request_count == 0

    def test_add_record(self):
        """Test adding a cost record."""
        usage = CostUsage()

        record = CostRecord(
            timestamp=datetime.now(UTC),
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            prompt_cost=0.03,
            completion_cost=0.03,
            total_cost=0.06,
        )

        usage.add(record)

        assert usage.prompt_tokens == 1000
        assert usage.completion_tokens == 500
        assert usage.total_tokens == 1500
        assert usage.total_cost == 0.06
        assert usage.request_count == 1

    def test_merge_usages(self):
        """Test merging two usage instances."""
        usage1 = CostUsage(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            total_cost=0.06,
            request_count=1,
        )

        usage2 = CostUsage(
            prompt_tokens=2000,
            completion_tokens=1000,
            total_tokens=3000,
            total_cost=0.12,
            request_count=2,
        )

        merged = usage1.merge(usage2)

        assert merged.prompt_tokens == 3000
        assert merged.completion_tokens == 1500
        assert merged.total_tokens == 4500
        assert merged.total_cost == 0.18
        assert merged.request_count == 3


class TestCostRecord:
    """Tests for CostRecord model."""

    def test_to_dict(self):
        """Test converting record to dictionary."""
        record = CostRecord(
            timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            prompt_cost=0.03,
            completion_cost=0.03,
            total_cost=0.06,
            execution_id="exec_123",
            workflow_id="wf_456",
        )

        data = record.to_dict()

        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"
        assert data["total_tokens"] == 1500
        assert data["total_cost"] == 0.06
        assert data["execution_id"] == "exec_123"


class TestCostTracker:
    """Tests for CostTracker."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "costs.db"

    @pytest.fixture
    def tracker(self, temp_db):
        """Create tracker with temp database."""
        config = CostConfig()
        return CostTracker(config=config, db_path=temp_db)

    def test_calculate_cost_openai_gpt4(self, tracker):
        """Test cost calculation for GPT-4."""
        prompt_cost, completion_cost, total_cost = tracker.calculate_cost(
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # GPT-4: $30/M input, $60/M output
        expected_prompt = (1000 / 1_000_000) * 30.0  # 0.03
        expected_completion = (500 / 1_000_000) * 60.0  # 0.03

        assert prompt_cost == pytest.approx(expected_prompt, rel=0.01)
        assert completion_cost == pytest.approx(expected_completion, rel=0.01)
        assert total_cost == pytest.approx(
            expected_prompt + expected_completion, rel=0.01
        )

    def test_track_usage(self, tracker):
        """Test tracking usage."""
        record = tracker.track_usage(
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        assert record.prompt_tokens == 1000
        assert record.completion_tokens == 500
        assert record.total_cost > 0

        # Check session usage
        session = tracker.get_session_usage()
        assert session.total_tokens == 1500
        assert session.request_count == 1

    def test_track_multiple_usages(self, tracker):
        """Test tracking multiple usages."""
        for _ in range(5):
            tracker.track_usage(
                provider="openai",
                model="gpt-4",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        session = tracker.get_session_usage()
        assert session.request_count == 5
        assert session.total_tokens == 7500

    def test_daily_usage(self, tracker):
        """Test getting daily usage."""
        tracker.track_usage(
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        daily = tracker.get_daily_usage()
        assert daily.request_count >= 1
        assert daily.total_tokens >= 1500

    def test_budget_warning_alert(self, temp_db):
        """Test budget warning alert generation."""
        config = CostConfig(
            budget=BudgetConfig(
                enabled=True,
                daily_limit=0.10,  # $0.10 daily limit
                warning_threshold=0.5,  # 50% warning
            )
        )
        tracker = CostTracker(config=config, db_path=temp_db)

        # Track usage that exceeds 50% of budget
        tracker.track_usage(
            provider="openai",
            model="gpt-4",
            prompt_tokens=2000,  # Will cost ~$0.06 (>50% of $0.10)
            completion_tokens=500,
        )

        alerts = tracker.get_pending_alerts()
        # Should have a warning alert
        assert len(alerts) >= 1
        valid_statuses = [BudgetStatus.WARNING, BudgetStatus.CRITICAL]
        assert alerts[0].status in valid_statuses

    def test_budget_exceeded_blocking(self, temp_db):
        """Test budget exceeded with blocking enabled."""
        config = CostConfig(
            budget=BudgetConfig(
                enabled=True,
                daily_limit=0.01,  # $0.01 daily limit
                block_on_exceed=True,
            )
        )
        tracker = CostTracker(config=config, db_path=temp_db)

        # First call should work - cost ~$0.006
        tracker.track_usage(
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )

        # Second call should exceed budget (total would be ~$0.012 > $0.01)
        with pytest.raises(BudgetExceededError) as exc_info:
            tracker.track_usage(
                provider="openai",
                model="gpt-4",
                prompt_tokens=100,
                completion_tokens=50,
            )

        assert "daily" in exc_info.value.budget_type

    def test_get_report(self, tracker):
        """Test generating cost report."""
        # Add some usage
        tracker.track_usage(
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
            workflow_id="wf_test",
        )

        report = tracker.get_report()

        assert isinstance(report, CostReport)
        assert report.total_usage.request_count >= 1
        assert report.budget_status == BudgetStatus.OK

    def test_estimate_cost(self, tracker):
        """Test cost estimation."""
        estimate = tracker.estimate_cost(
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            estimated_completion_tokens=500,
        )

        # GPT-4: $30/M input, $60/M output
        expected = (1000 / 1_000_000) * 30.0 + (500 / 1_000_000) * 60.0
        assert estimate == pytest.approx(expected, rel=0.01)

    def test_would_exceed_budget(self, temp_db):
        """Test budget check before execution."""
        config = CostConfig(
            budget=BudgetConfig(
                enabled=True,
                daily_limit=0.05,
            )
        )
        tracker = CostTracker(config=config, db_path=temp_db)

        # Check if small cost would exceed
        would_exceed, budget_type = tracker.would_exceed_budget(0.01)
        assert would_exceed is False

        # Check if large cost would exceed
        would_exceed, budget_type = tracker.would_exceed_budget(0.10)
        assert would_exceed is True
        assert budget_type == "daily"

    def test_tracking_disabled(self, temp_db):
        """Test tracker with tracking disabled."""
        config = CostConfig(tracking=TrackingConfig(enabled=False))
        tracker = CostTracker(config=config, db_path=temp_db)

        record = tracker.track_usage(
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Should return zero-cost record
        assert record.total_cost == 0.0


class TestBudgetAlert:
    """Tests for BudgetAlert model."""

    def test_to_dict(self):
        """Test converting alert to dictionary."""
        alert = BudgetAlert(
            timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
            status=BudgetStatus.WARNING,
            budget_type="daily",
            budget_limit=10.0,
            current_usage=8.5,
            usage_percent=0.85,
            message="Budget warning: 85% used",
        )

        data = alert.to_dict()

        assert data["status"] == "warning"
        assert data["budget_type"] == "daily"
        assert data["usage_percent"] == 0.85


class TestExecutionCost:
    """Tests for ExecutionCost model in context."""

    def test_execution_cost_tracking(self):
        """Test execution cost tracking."""
        from paracle_orchestration.context import ExecutionCost

        cost = ExecutionCost()

        cost.add_step_cost(
            step_id="step_1",
            prompt_tokens=1000,
            completion_tokens=500,
            prompt_cost=0.03,
            completion_cost=0.03,
            provider="openai",
            model="gpt-4",
        )

        assert cost.total_tokens == 1500
        assert cost.total_cost == 0.06
        assert cost.request_count == 1
        assert "step_1" in cost.step_costs

    def test_execution_context_with_cost(self):
        """Test execution context includes cost."""
        from paracle_orchestration.context import ExecutionContext

        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={"query": "test"},
        )

        assert context.cost is not None
        assert context.cost.total_cost == 0.0

        # Add step cost
        context.cost.add_step_cost(
            step_id="step_1",
            prompt_tokens=1000,
            completion_tokens=500,
            prompt_cost=0.03,
            completion_cost=0.03,
        )

        assert context.cost.total_cost == 0.06
