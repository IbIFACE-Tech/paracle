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
        circuit = CircuitBreaker("test_service", failure_threshold=5, timeout=60)
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
