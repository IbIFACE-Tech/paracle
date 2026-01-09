"""Unit tests for paracle_meta.capabilities.provider_chain module."""

import pytest
from paracle_meta.capabilities.provider_chain import (
    CircuitBreaker,
    FallbackStrategy,
    ProviderChain,
    ProviderChainError,
    ProviderMetrics,
)
from paracle_meta.capabilities.provider_protocol import LLMRequest
from paracle_meta.capabilities.providers.mock import (
    FailingMockProvider,
    MockProvider,
    RecordingMockProvider,
)


class TestProviderMetrics:
    """Tests for ProviderMetrics."""

    def test_default_values(self):
        """Test default metric values."""
        metrics = ProviderMetrics()

        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.total_requests == 0
        assert metrics.success_rate == 1.0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = ProviderMetrics(success_count=8, failure_count=2)

        assert metrics.total_requests == 10
        assert metrics.success_rate == 0.8

    def test_avg_latency(self):
        """Test average latency calculation."""
        metrics = ProviderMetrics(success_count=4, total_latency_ms=400.0)

        assert metrics.avg_latency_ms == 100.0

    def test_avg_latency_zero_success(self):
        """Test average latency with no successes."""
        metrics = ProviderMetrics(success_count=0)

        assert metrics.avg_latency_ms == 0.0


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_initial_state_closed(self):
        """Test circuit starts closed."""
        cb = CircuitBreaker()

        assert cb.is_open("test") is False
        assert cb.get_state("test") == "closed"

    def test_opens_after_failures(self):
        """Test circuit opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure("test")
        assert cb.is_open("test") is False

        cb.record_failure("test")
        assert cb.is_open("test") is False

        cb.record_failure("test")
        assert cb.is_open("test") is True
        assert cb.get_state("test") == "open"

    def test_success_resets_failures(self):
        """Test success resets failure count."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure("test")
        cb.record_failure("test")
        cb.record_success("test")

        # Should reset, not open
        cb.record_failure("test")
        assert cb.is_open("test") is False

    def test_reset_clears_state(self):
        """Test reset clears all state."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure("test")

        cb.reset("test")
        assert cb.is_open("test") is False
        assert cb.get_state("test") == "closed"


class TestFallbackStrategy:
    """Tests for FallbackStrategy enum."""

    def test_strategy_values(self):
        """Test strategy enum values."""
        assert FallbackStrategy.PRIMARY_WITH_FALLBACK.value == "primary_with_fallback"
        assert FallbackStrategy.ROUND_ROBIN.value == "round_robin"
        assert FallbackStrategy.COST_OPTIMIZED.value == "cost_optimized"
        assert FallbackStrategy.QUALITY_FIRST.value == "quality_first"
        assert FallbackStrategy.RANDOM.value == "random"


class TestProviderChain:
    """Tests for ProviderChain."""

    @pytest.fixture
    def mock_providers(self):
        """Create mock providers."""
        return [
            MockProvider(model="primary"),
            MockProvider(model="secondary"),
            MockProvider(model="tertiary"),
        ]

    @pytest.fixture
    def chain(self, mock_providers):
        """Create provider chain."""
        return ProviderChain(
            providers=mock_providers,
            strategy=FallbackStrategy.PRIMARY_WITH_FALLBACK,
        )

    @pytest.mark.asyncio
    async def test_initialization(self, chain):
        """Test chain initialization."""
        await chain.initialize()

        assert chain.is_available is True
        assert len(chain.providers) == 3

    @pytest.mark.asyncio
    async def test_complete_uses_first_provider(self, chain):
        """Test complete uses first available provider."""
        await chain.initialize()

        request = LLMRequest(prompt="Hello")
        response = await chain.complete(request)

        assert response.content is not None
        assert response.provider == "mock"

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self):
        """Test fallback to next provider on failure."""
        failing = FailingMockProvider()
        working = RecordingMockProvider()

        chain = ProviderChain(
            providers=[failing, working],
            strategy=FallbackStrategy.PRIMARY_WITH_FALLBACK,
        )
        await chain.initialize()

        request = LLMRequest(prompt="Hello")
        response = await chain.complete(request)

        # Should have fallen back to working provider
        assert len(working.history) == 1
        assert response.provider == "mock"

    @pytest.mark.asyncio
    async def test_all_fail_raises_chain_error(self):
        """Test error when all providers fail."""
        providers = [
            FailingMockProvider(error_message="Error 1"),
            FailingMockProvider(error_message="Error 2"),
        ]

        chain = ProviderChain(providers=providers)
        await chain.initialize()

        request = LLMRequest(prompt="Hello")

        with pytest.raises(ProviderChainError) as exc_info:
            await chain.complete(request)

        assert len(exc_info.value.errors) == 2

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, chain):
        """Test metrics are tracked."""
        await chain.initialize()

        request = LLMRequest(prompt="Hello")
        await chain.complete(request)

        metrics = chain.get_metrics("mock")
        assert metrics.success_count >= 1

    @pytest.mark.asyncio
    async def test_round_robin_strategy(self):
        """Test round robin distributes requests."""
        providers = [
            RecordingMockProvider(model="p1"),
            RecordingMockProvider(model="p2"),
        ]

        chain = ProviderChain(
            providers=providers,
            strategy=FallbackStrategy.ROUND_ROBIN,
        )
        await chain.initialize()

        request = LLMRequest(prompt="Test")

        # Make multiple requests
        await chain.complete(request)
        await chain.complete(request)
        await chain.complete(request)

        # Both providers should have been used
        total_calls = sum(len(p.history) for p in providers)
        assert total_calls == 3

    @pytest.mark.asyncio
    async def test_shutdown(self, chain):
        """Test chain shutdown."""
        await chain.initialize()
        await chain.shutdown()

        assert chain.is_available is False


class TestProviderChainWithCircuitBreaker:
    """Tests for provider chain with circuit breaker."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_skips_failing_provider(self):
        """Test circuit breaker skips failing providers."""
        failing = FailingMockProvider()
        working = RecordingMockProvider()

        cb = CircuitBreaker(failure_threshold=2, reset_timeout_seconds=1)

        chain = ProviderChain(
            providers=[failing, working],
            circuit_breaker=cb,
        )
        await chain.initialize()

        request = LLMRequest(prompt="Hello")

        # First two requests hit failing provider
        await chain.complete(request)
        await chain.complete(request)

        # Now circuit should be open, third request skips failing
        await chain.complete(request)

        # Circuit should be open for failing provider
        assert cb.is_open("failing_mock") is True
