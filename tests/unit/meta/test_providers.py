"""Unit tests for paracle_meta.providers module."""

import pytest
from paracle_meta.exceptions import ProviderNotAvailableError
from paracle_meta.providers import (
    ProviderConfig,
    ProviderOrchestrator,
    ProviderSelection,
    ProviderSelector,
    TaskType,
)


class TestProviderConfig:
    """Tests for ProviderConfig model."""

    def test_create_minimal_config(self):
        """Test creating config with minimal required fields."""
        config = ProviderConfig(name="test", model="gpt-4")
        assert config.name == "test"
        assert config.model == "gpt-4"
        assert config.enabled is True
        assert config.priority == 10

    def test_create_full_config(self):
        """Test creating config with all fields."""
        config = ProviderConfig(
            name="anthropic",
            model="claude-sonnet-4-20250514",
            api_key_env="ANTHROPIC_API_KEY",
            use_for=["agent", "security"],
            priority=1,
            cost_per_1k_tokens=0.003,
            max_tokens=8192,
            enabled=True,
        )
        assert config.name == "anthropic"
        assert config.use_for == ["agent", "security"]
        assert config.cost_per_1k_tokens == 0.003


class TestProviderOrchestrator:
    """Tests for ProviderOrchestrator."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator with temp config."""
        # Will use defaults since config doesn't exist
        return ProviderOrchestrator(config_path=tmp_path / "config.yaml")

    def test_initialization_with_defaults(self, orchestrator):
        """Test initialization loads default providers."""
        assert len(orchestrator.available_providers) > 0
        assert "anthropic" in orchestrator.available_providers
        assert "openai" in orchestrator.available_providers

    def test_select_provider_simple_task(self, orchestrator):
        """Test selecting provider for simple task."""
        selection = orchestrator.select_provider(
            task_type=TaskType.SIMPLE, complexity=0.2
        )
        assert isinstance(selection, ProviderSelection)
        assert selection.provider in orchestrator.available_providers

    def test_select_provider_complex_task(self, orchestrator):
        """Test selecting provider for complex task."""
        selection = orchestrator.select_provider(
            task_type=TaskType.COMPLEX, complexity=0.9
        )
        assert selection.provider in ["anthropic", "openai"]

    def test_select_provider_with_task_type_match(self, orchestrator):
        """Test provider selection considers task type affinity."""
        selection = orchestrator.select_provider(task_type="agent", complexity=0.5)
        # Anthropic should be preferred for agents
        assert selection.provider in orchestrator.available_providers

    def test_get_provider_config(self, orchestrator):
        """Test getting provider config."""
        config = orchestrator.get_provider_config("anthropic")
        assert config.name == "anthropic"
        assert config.model is not None

    def test_get_provider_config_not_found(self, orchestrator):
        """Test error when provider not found."""
        with pytest.raises(ProviderNotAvailableError) as exc_info:
            orchestrator.get_provider_config("nonexistent")
        assert exc_info.value.details["provider"] == "nonexistent"

    def test_record_request(self, orchestrator):
        """Test recording request for performance tracking."""
        orchestrator.record_request(
            provider="anthropic",
            model="claude-sonnet-4",
            tokens=1000,
            cost=0.003,
            quality_score=8.5,
            latency_ms=500,
            success=True,
        )
        # Should not raise

    @pytest.mark.asyncio
    async def test_get_performance_stats(self, orchestrator):
        """Test getting performance statistics."""
        # Record some requests
        orchestrator.record_request(
            provider="anthropic",
            model="claude-sonnet-4",
            tokens=1000,
            cost=0.003,
            quality_score=8.5,
            latency_ms=500,
            success=True,
        )
        orchestrator.record_request(
            provider="anthropic",
            model="claude-sonnet-4",
            tokens=500,
            cost=0.0015,
            quality_score=9.0,
            latency_ms=300,
            success=True,
        )

        stats = await orchestrator.get_performance_stats()
        assert "anthropic/claude-sonnet-4" in stats
        assert stats["anthropic/claude-sonnet-4"]["total_requests"] == 2

    def test_filter_providers(self, tmp_path):
        """Test filtering providers."""
        orchestrator = ProviderOrchestrator(
            providers=["anthropic"], config_path=tmp_path / "config.yaml"
        )
        # Selection should only return anthropic
        selection = orchestrator.select_provider(task_type="agent", complexity=0.5)
        assert selection.provider == "anthropic"


class TestProviderSelector:
    """Tests for ProviderSelector helper."""

    @pytest.fixture
    def selector(self, tmp_path):
        """Create selector with orchestrator."""
        orchestrator = ProviderOrchestrator(config_path=tmp_path / "config.yaml")
        return ProviderSelector(orchestrator)

    def test_select_for_task(self, selector):
        """Test selecting provider for task."""
        selection = selector.select_for_task(task_type="agent", complexity=0.5)
        assert selection.provider is not None

    def test_select_with_budget(self, selector):
        """Test selecting with budget constraint."""
        selection = selector.select_for_task(
            task_type="simple", complexity=0.2, budget_remaining=0.50
        )
        # Should select a provider within budget
        assert selection.cost_per_1k <= 0.05  # 10% of budget

    def test_get_fallback_chain(self, selector):
        """Test getting fallback chain."""
        chain = selector.get_fallback_chain("agent")
        assert len(chain) > 0
        # Affinity providers should come first
        assert "anthropic" in chain or "openai" in chain


class TestTaskType:
    """Tests for TaskType enum."""

    def test_task_type_values(self):
        """Test task type values."""
        assert TaskType.AGENT.value == "agent"
        assert TaskType.WORKFLOW.value == "workflow"
        assert TaskType.SIMPLE.value == "simple"
        assert TaskType.COMPLEX.value == "complex"
