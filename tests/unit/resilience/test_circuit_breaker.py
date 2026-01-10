"""Tests for circuit breaker pattern."""

import time

import pytest
from paracle_resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitOpenError,
)


class TestCircuitBreakerBasics:
    """Test basic circuit breaker functionality."""

    def test_circuit_breaker_creation(self):
        """Test circuit breaker initialization."""
        circuit = CircuitBreaker(
            "test_service", failure_threshold=5, timeout=60)
        assert circuit.name == "test_service"
        assert circuit.state == CircuitBreakerState.CLOSED
        assert circuit.failure_count == 0
        assert circuit.config.failure_threshold == 5
        assert circuit.config.timeout == 60

    def test_circuit_closed_success(self):
        """Test successful call with closed circuit."""
        circuit = CircuitBreaker("test", failure_threshold=3)

        def success_func():
            return "success"

        result = circuit.call(success_func)
        assert result == "success"
        assert circuit.state == CircuitBreakerState.CLOSED
        assert circuit.failure_count == 0

    def test_circuit_closed_failure(self):
        """Test failed call with closed circuit."""
        circuit = CircuitBreaker("test", failure_threshold=3)

        def failure_func():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            circuit.call(failure_func)

        assert (
            circuit.state == CircuitBreakerState.CLOSED
        )  # Still closed after 1 failure
        assert circuit.failure_count == 1


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions."""

    def test_open_after_threshold(self):
        """Test circuit opens after failure threshold."""
        circuit = CircuitBreaker("test", failure_threshold=3, timeout=60)

        def failure_func():
            raise ValueError("fail")

        # Trigger 3 failures
        for _ in range(3):
            with pytest.raises(ValueError):
                circuit.call(failure_func)

        assert circuit.state == CircuitBreakerState.OPEN
        assert circuit.opened_at is not None

    def test_open_circuit_rejects_calls(self):
        """Test open circuit rejects new calls."""
        circuit = CircuitBreaker("test", failure_threshold=2, timeout=60)

        def failure_func():
            raise ValueError("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                circuit.call(failure_func)

        # Next call should be rejected
        with pytest.raises(CircuitOpenError) as exc_info:
            circuit.call(lambda: "success")

        assert "Circuit breaker is OPEN" in str(exc_info.value)
        assert exc_info.value.circuit_name == "test"

    def test_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        circuit = CircuitBreaker(
            "test", failure_threshold=2, timeout=0.1
        )  # 100ms timeout

        def failure_func():
            raise ValueError("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                circuit.call(failure_func)

        assert circuit.state == CircuitBreakerState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # Next call should attempt half-open
        def success_func():
            return "success"

        result = circuit.call(success_func)
        assert result == "success"
        assert circuit.state == CircuitBreakerState.HALF_OPEN

    def test_close_after_half_open_successes(self):
        """Test circuit closes after success threshold in half-open."""
        circuit = CircuitBreaker(
            "test",
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1,
        )

        def failure_func():
            raise ValueError("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                circuit.call(failure_func)

        # Wait and succeed twice
        time.sleep(0.15)

        def success_func():
            return "success"

        circuit.call(success_func)
        assert circuit.state == CircuitBreakerState.HALF_OPEN

        circuit.call(success_func)
        assert circuit.state == CircuitBreakerState.CLOSED
        assert circuit.failure_count == 0

    def test_reopen_on_half_open_failure(self):
        """Test circuit reopens if failure during half-open."""
        circuit = CircuitBreaker("test", failure_threshold=2, timeout=0.1)

        def failure_func():
            raise ValueError("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                circuit.call(failure_func)

        # Wait and fail again
        time.sleep(0.15)

        with pytest.raises(ValueError):
            circuit.call(failure_func)

        assert circuit.state == CircuitBreakerState.OPEN


class TestCircuitBreakerContextManager:
    """Test circuit breaker as context manager."""

    def test_context_manager_success(self):
        """Test context manager with successful operation."""
        circuit = CircuitBreaker("test")

        with circuit:
            result = "success"

        assert circuit.failure_count == 0

    def test_context_manager_failure(self):
        """Test context manager with failed operation."""
        circuit = CircuitBreaker("test", failure_threshold=3)

        with pytest.raises(ValueError):
            with circuit:
                raise ValueError("fail")

        assert circuit.failure_count == 1

    def test_context_manager_open_circuit(self):
        """Test context manager rejects when circuit open."""
        circuit = CircuitBreaker("test", failure_threshold=1)

        # Open circuit
        with pytest.raises(ValueError):
            with circuit:
                raise ValueError("fail")

        # Should reject
        with pytest.raises(CircuitOpenError):
            with circuit:
                pass


@pytest.mark.asyncio
class TestCircuitBreakerAsync:
    """Test async circuit breaker functionality."""

    async def test_async_success(self):
        """Test async successful call."""
        circuit = CircuitBreaker("test")

        async def async_success():
            return "async_success"

        result = await circuit.call_async(async_success)
        assert result == "async_success"
        assert circuit.failure_count == 0

    async def test_async_failure(self):
        """Test async failed call."""
        circuit = CircuitBreaker("test", failure_threshold=3)

        async def async_failure():
            raise ValueError("async_fail")

        with pytest.raises(ValueError):
            await circuit.call_async(async_failure)

        assert circuit.failure_count == 1

    async def test_async_context_manager(self):
        """Test async context manager."""
        circuit = CircuitBreaker("test")

        async with circuit:
            result = "async_success"

        assert circuit.failure_count == 0

    async def test_async_open_circuit(self):
        """Test async open circuit rejection."""
        circuit = CircuitBreaker("test", failure_threshold=2)

        async def async_failure():
            raise ValueError("fail")

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.call_async(async_failure)

        # Should reject
        with pytest.raises(CircuitOpenError):
            await circuit.call_async(lambda: "success")


class TestCircuitBreakerReset:
    """Test circuit breaker reset functionality."""

    def test_manual_reset(self):
        """Test manual circuit reset."""
        circuit = CircuitBreaker("test", failure_threshold=2)

        def failure_func():
            raise ValueError("fail")

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                circuit.call(failure_func)

        assert circuit.state == CircuitBreakerState.OPEN

        # Reset
        circuit.reset()
        assert circuit.state == CircuitBreakerState.CLOSED
        assert circuit.failure_count == 0
        assert circuit.opened_at is None

    def test_get_state(self):
        """Test get_state returns correct information."""
        circuit = CircuitBreaker("test", failure_threshold=5, timeout=60)

        state = circuit.get_state()
        assert state["name"] == "test"
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert state["config"]["failure_threshold"] == 5
        assert state["config"]["timeout"] == 60


class TestCircuitBreakerConfiguration:
    """Test circuit breaker configuration."""

    def test_custom_thresholds(self):
        """Test custom failure and success thresholds."""
        circuit = CircuitBreaker(
            "test",
            failure_threshold=10,
            success_threshold=5,
        )

        assert circuit.config.failure_threshold == 10
        assert circuit.config.success_threshold == 5

    def test_custom_timeout(self):
        """Test custom timeout configuration."""
        circuit = CircuitBreaker("test", timeout=120.0)
        assert circuit.config.timeout == 120.0

    def test_half_open_max_calls(self):
        """Test half-open max calls limit."""
        circuit = CircuitBreaker(
            "test",
            failure_threshold=1,
            timeout=0.1,
            half_open_max_calls=2,
        )

        # Open circuit
        with pytest.raises(ZeroDivisionError):
            circuit.call(lambda: 1 / 0)

        # Wait for timeout
        time.sleep(0.15)

        # Should allow 2 calls in half-open
        circuit.half_open_calls = 2
        circuit.state = CircuitBreakerState.HALF_OPEN

        # 3rd call should be rejected
        with pytest.raises(CircuitOpenError):
            circuit.call(lambda: "success")


class TestCircuitBreakerMetrics:
    """Test circuit breaker metrics tracking."""

    def test_metrics_initialization(self):
        """Test that metrics are initialized to zero."""
        circuit = CircuitBreaker("test", failure_threshold=3)
        state = circuit.get_state()

        assert "metrics" in state
        metrics = state["metrics"]
        assert metrics["total_calls"] == 0
        assert metrics["total_successes"] == 0
        assert metrics["total_failures"] == 0
        assert metrics["total_rejected"] == 0
        assert metrics["success_rate"] == 0.0
        assert metrics["failure_rate"] == 0.0
        assert metrics["rejection_rate"] == 0.0

    def test_metrics_successful_calls(self):
        """Test metrics tracking for successful calls."""
        circuit = CircuitBreaker("test", failure_threshold=3)

        # Execute 5 successful calls
        for _ in range(5):
            result = circuit.call(lambda: "success")
            assert result == "success"

        state = circuit.get_state()
        metrics = state["metrics"]

        assert metrics["total_calls"] == 5
        assert metrics["total_successes"] == 5
        assert metrics["total_failures"] == 0
        assert metrics["total_rejected"] == 0
        assert metrics["success_rate"] == 1.0
        assert metrics["failure_rate"] == 0.0

    def test_metrics_failed_calls(self):
        """Test metrics tracking for failed calls."""
        circuit = CircuitBreaker("test", failure_threshold=5)

        # Execute 3 failed calls (not enough to open circuit)
        for _ in range(3):
            with pytest.raises(ValueError):
                circuit.call(lambda: (_ for _ in ()).throw(
                    ValueError("error")))

        state = circuit.get_state()
        metrics = state["metrics"]

        assert metrics["total_calls"] == 3
        assert metrics["total_successes"] == 0
        assert metrics["total_failures"] == 3
        assert metrics["total_rejected"] == 0
        assert metrics["success_rate"] == 0.0
        assert metrics["failure_rate"] == 1.0

    def test_metrics_mixed_calls(self):
        """Test metrics with mixed successful and failed calls."""
        circuit = CircuitBreaker("test", failure_threshold=10)

        # 7 successful calls
        for _ in range(7):
            circuit.call(lambda: "success")

        # 3 failed calls
        for _ in range(3):
            with pytest.raises(ValueError):
                circuit.call(lambda: (_ for _ in ()).throw(
                    ValueError("error")))

        state = circuit.get_state()
        metrics = state["metrics"]

        assert metrics["total_calls"] == 10
        assert metrics["total_successes"] == 7
        assert metrics["total_failures"] == 3
        assert metrics["success_rate"] == 0.7
        assert metrics["failure_rate"] == 0.3

    def test_metrics_rejected_calls(self):
        """Test metrics tracking for rejected calls when circuit is open."""
        circuit = CircuitBreaker("test", failure_threshold=3, timeout=1)

        # Open the circuit with 3 failures
        for _ in range(3):
            with pytest.raises(ValueError):
                circuit.call(lambda: (_ for _ in ()).throw(
                    ValueError("error")))

        assert circuit.state == CircuitBreakerState.OPEN

        # Try 5 calls while circuit is open (all should be rejected)
        for _ in range(5):
            with pytest.raises(CircuitOpenError):
                circuit.call(lambda: "success")

        state = circuit.get_state()
        metrics = state["metrics"]

        assert metrics["total_calls"] == 3  # Only calls that were attempted
        assert metrics["total_failures"] == 3
        assert metrics["total_rejected"] == 5  # Rejected while open

        # Rejection rate calculation: rejected / (calls + rejected)
        total_requests = metrics["total_calls"] + metrics["total_rejected"]
        assert metrics["rejection_rate"] == metrics["total_rejected"] / \
            total_requests

    def test_metrics_rate_calculations(self):
        """Test that rate calculations are accurate."""
        circuit = CircuitBreaker("test", failure_threshold=100)

        # 60 successes
        for _ in range(60):
            circuit.call(lambda: "success")

        # 30 failures (threshold is 100, so won't open)
        for _ in range(30):
            with pytest.raises(ValueError):
                circuit.call(lambda: (_ for _ in ()).throw(
                    ValueError("error")))

        # Verify metrics before forcing rejections
        state = circuit.get_state()
        assert state["state"] == "closed"  # Should still be closed

        # Force some rejections by manually opening circuit
        circuit.state = CircuitBreakerState.OPEN
        circuit.opened_at = circuit.last_failure_time

        for _ in range(10):
            with pytest.raises(CircuitOpenError):
                circuit.call(lambda: "success")

        state = circuit.get_state()
        metrics = state["metrics"]

        assert metrics["total_calls"] == 90
        assert metrics["total_successes"] == 60
        assert metrics["total_failures"] == 30
        assert metrics["total_rejected"] == 10

        # Verify rate calculations
        assert abs(metrics["success_rate"] - (60 / 90)) < 0.01
        assert abs(metrics["failure_rate"] - (30 / 90)) < 0.01
        assert abs(metrics["rejection_rate"] - (10 / 100)) < 0.01

    def test_metrics_half_open_state(self):
        """Test metrics tracking during half-open state."""
        circuit = CircuitBreaker(
            "test",
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1
        )

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                circuit.call(lambda: (_ for _ in ()).throw(
                    ValueError("error")))

        assert circuit.state == CircuitBreakerState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # Reset to half-open (happens on next call attempt)
        circuit._half_open()

        # Execute 2 successful calls to close circuit
        circuit.call(lambda: "success")
        circuit.call(lambda: "success")

        assert circuit.state == CircuitBreakerState.CLOSED

        state = circuit.get_state()
        metrics = state["metrics"]

        # Should track all successful calls including half-open period
        assert metrics["total_successes"] == 2
        assert metrics["total_failures"] == 2
        assert metrics["total_calls"] == 4

    def test_metrics_persistence_across_state_changes(self):
        """Test that metrics persist across circuit state transitions."""
        circuit = CircuitBreaker("test", failure_threshold=2, timeout=0.1)

        # Initial successes (CLOSED)
        for _ in range(5):
            circuit.call(lambda: "success")

        # Failures to open circuit (CLOSED -> OPEN)
        for _ in range(2):
            with pytest.raises(ValueError):
                circuit.call(lambda: (_ for _ in ()).throw(
                    ValueError("error")))

        # Rejections while open
        for _ in range(3):
            with pytest.raises(CircuitOpenError):
                circuit.call(lambda: "success")

        # Wait and transition to half-open
        time.sleep(0.15)
        circuit._half_open()

        # More successes (HALF_OPEN -> CLOSED)
        for _ in range(3):
            circuit.call(lambda: "success")

        state = circuit.get_state()
        metrics = state["metrics"]

        # Metrics should accumulate across all states
        assert metrics["total_calls"] == 10  # 5 + 2 + 3
        assert metrics["total_successes"] == 8  # 5 + 3
        assert metrics["total_failures"] == 2
        assert metrics["total_rejected"] == 3
