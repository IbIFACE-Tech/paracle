"""Unit tests for paracle_meta.optimizer module."""

import pytest

from paracle_meta.optimizer import (
    CostConfig,
    CostOptimizer,
    CostRecord,
    CostReport,
    QualityScorer,
)


class TestCostConfig:
    """Tests for CostConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CostConfig()
        assert config.enabled is True
        assert config.max_daily_budget == 10.0
        assert config.max_monthly_budget == 100.0
        assert config.warn_at_percent == 80

    def test_custom_config(self):
        """Test custom configuration."""
        config = CostConfig(
            max_daily_budget=5.0,
            max_monthly_budget=50.0,
            prefer_cheaper_for_simple=False,
        )
        assert config.max_daily_budget == 5.0
        assert config.prefer_cheaper_for_simple is False


class TestCostOptimizer:
    """Tests for CostOptimizer."""

    @pytest.fixture
    def optimizer(self, tmp_path):
        """Create optimizer with temp database."""
        return CostOptimizer(enabled=True, db_path=tmp_path / "costs.db")

    @pytest.fixture
    def disabled_optimizer(self, tmp_path):
        """Create disabled optimizer."""
        return CostOptimizer(enabled=False, db_path=tmp_path / "costs.db")

    def test_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer.enabled is True
        assert optimizer.config is not None

    def test_disabled_optimizer(self, disabled_optimizer):
        """Test disabled optimizer behavior."""
        result = disabled_optimizer.select_provider(task_type="agent", complexity=0.5)
        assert result["provider"] == "anthropic"
        assert "disabled" in result["reason"].lower()

    def test_select_provider_simple(self, optimizer):
        """Test provider selection for simple task."""
        result = optimizer.select_provider(task_type="simple", complexity=0.2)
        assert result["provider"] == "ollama"  # Free for simple tasks

    def test_select_provider_medium(self, optimizer):
        """Test provider selection for medium task."""
        result = optimizer.select_provider(task_type="agent", complexity=0.5)
        assert result["provider"] == "openai"

    def test_select_provider_complex(self, optimizer):
        """Test provider selection for complex task."""
        result = optimizer.select_provider(task_type="complex", complexity=0.9)
        assert result["provider"] == "anthropic"

    def test_can_afford_within_budget(self, optimizer):
        """Test afford check within budget."""
        can_afford, reason = optimizer.can_afford(0.05)
        assert can_afford is True
        assert "Within budget" in reason

    @pytest.mark.asyncio
    async def test_track_cost(self, optimizer):
        """Test cost tracking."""

        class MockResult:
            id = "gen_123"
            provider = "anthropic"
            model = "claude-sonnet-4"
            tokens_input = 1000
            tokens_output = 500
            cost_usd = 0.003

        await optimizer.track_cost(MockResult())

        stats = await optimizer.get_statistics()
        assert stats["total_cost"] == 0.003

    @pytest.mark.asyncio
    async def test_get_statistics(self, optimizer):
        """Test getting statistics."""
        stats = await optimizer.get_statistics()
        assert "daily_cost" in stats
        assert "monthly_cost" in stats
        assert "total_cost" in stats

    @pytest.mark.asyncio
    async def test_get_report(self, optimizer):
        """Test getting cost report."""
        report = await optimizer.get_report("daily")
        assert isinstance(report, CostReport)
        assert report.period == "daily"

    @pytest.mark.asyncio
    async def test_get_statistics_disabled(self, disabled_optimizer):
        """Test statistics when disabled."""
        stats = await disabled_optimizer.get_statistics()
        assert stats == {"enabled": False}


class TestQualityScorer:
    """Tests for QualityScorer."""

    @pytest.fixture
    def scorer(self):
        """Create quality scorer."""
        return QualityScorer()

    @pytest.mark.asyncio
    async def test_score_agent(self, scorer):
        """Test scoring agent content."""

        class MockResult:
            artifact_type = "agent"
            content = """
name: TestAgent
role: Test role for testing

system_prompt: |
  You are a test agent.

capabilities:
  - Testing things
  - Doing tests
"""

        score = await scorer.score(MockResult())
        assert 0 <= score <= 10

    @pytest.mark.asyncio
    async def test_score_workflow(self, scorer):
        """Test scoring workflow content."""

        class MockResult:
            artifact_type = "workflow"
            content = """
name: TestWorkflow
steps:
  - id: step1
    agent: TestAgent
inputs:
  - name: input1
outputs:
  - name: output1
"""

        score = await scorer.score(MockResult())
        assert 0 <= score <= 10

    @pytest.mark.asyncio
    async def test_score_with_examples(self, scorer):
        """Test that examples improve score."""

        class ResultWithExamples:
            artifact_type = "skill"
            content = """
# Test Skill

Example usage:
```python
# Example code here
```

More examples included.
"""

        class ResultWithoutExamples:
            artifact_type = "skill"
            content = """
# Test Skill

Basic content only.
"""

        score_with = await scorer.score(ResultWithExamples())
        score_without = await scorer.score(ResultWithoutExamples())
        # Content with examples should score higher
        assert score_with >= score_without

    @pytest.mark.asyncio
    async def test_score_penalizes_todo(self, scorer):
        """Test that TODO comments reduce score."""

        class ResultWithTodo:
            artifact_type = "agent"
            content = """
name: TestAgent
role: Test

TODO: Implement this later
FIXME: This is broken
"""

        score = await scorer.score(ResultWithTodo())
        # Score should be lower due to TODO/FIXME
        assert score < 8.0


class TestCostRecord:
    """Tests for CostRecord model."""

    def test_create_cost_record(self):
        """Test creating a cost record."""
        record = CostRecord(
            generation_id="gen_123",
            provider="anthropic",
            model="claude-sonnet-4",
            tokens_input=1000,
            tokens_output=500,
            cost_usd=0.003,
        )
        assert record.generation_id == "gen_123"
        assert record.cost_usd == 0.003
        assert record.timestamp is not None
