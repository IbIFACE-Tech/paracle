"""Unit tests for ResilienceCapability (circuit breaker, retry, fallback)."""

import asyncio

import pytest

from paracle_meta.capabilities.resilience import (
    CircuitBreaker,
    CircuitState,
    ResilienceCapability,
    ResilienceConfig,
    RetryStrategy,
)


# --- Test Fixtures ---


@pytest.fixture
def resilience_config():
    """Create default resilience configuration."""
    return ResilienceConfig(
        circuit_breaker_enabled=True,
        failure_threshold=3,
        recovery_timeout_seconds=2,
        success_threshold=2,
        retry_enabled=True,
        max_retries=3,
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        initial_retry_delay_ms=100,
        max_retry_delay_ms=10000,
        fallback_enabled=True,
        timeout_seconds=5.0,
        bulkhead_enabled=False,
        max_concurrent_calls=100,
    )


@pytest.fixture
def resilience(resilience_config):
    """Create ResilienceCapability instance."""
    return ResilienceCapability(resilience_config)


@pytest.fixture
def circuit_breaker(resilience_config):
    """Create CircuitBreaker instance."""
    return CircuitBreaker(
        failure_threshold=resilience_config.failure_threshold,
        recovery_timeout_seconds=(
            resilience_config.recovery_timeout_seconds
        ),
        success_threshold=resilience_config.success_threshold,
    )


# --- CircuitBreaker Tests ---


def test_circuit_breaker_initial_state(circuit_breaker):
    """Test circuit breaker initializes in CLOSED state."""
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 0
    assert circuit_breaker.success_count == 0


@pytest.mark.asyncio
async def test_circuit_breaker_successful_call(circuit_breaker):
    """Test successful operation through circuit breaker."""

    async def successful_operation():
        return "success"

    result = await circuit_breaker.call(successful_operation)
    assert result == "success"
    assert circuit_breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_failures(circuit_breaker):
    """Test circuit breaker opens after failure threshold."""

    async def failing_operation():
        raise Exception("Simulated failure")

    # Execute failures up to threshold
    for _ in range(circuit_breaker.failure_threshold):
        with pytest.raises(Exception, match="Simulated failure"):
            await circuit_breaker.call(failing_operation)

    # Circuit should be OPEN now
    assert circuit_breaker.state == CircuitState.OPEN
    assert circuit_breaker.failure_count == circuit_breaker.failure_threshold


@pytest.mark.asyncio
async def test_circuit_breaker_rejects_when_open(circuit_breaker):
    """Test circuit breaker rejects calls when OPEN."""

    async def failing_operation():
        raise Exception("Simulated failure")

    # Open the circuit
    for _ in range(circuit_breaker.failure_threshold):
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_operation)

    # Next call should be rejected immediately
    async def any_operation():
        return "should not execute"

    with pytest.raises(Exception, match="Circuit breaker OPEN"):
        await circuit_breaker.call(any_operation)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_after_timeout(circuit_breaker):
    """Test circuit breaker transitions to HALF_OPEN after recovery timeout."""

    async def failing_operation():
        raise Exception("Simulated failure")

    # Open the circuit
    for _ in range(circuit_breaker.failure_threshold):
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_operation)

    assert circuit_breaker.state == CircuitState.OPEN

    # Wait for recovery timeout (2 seconds)
    await asyncio.sleep(2.5)

    # Check state transitions to HALF_OPEN
    state = circuit_breaker._get_state()
    assert state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_closes_from_half_open(circuit_breaker):
    """Test circuit breaker closes from HALF_OPEN after successful calls."""

    async def failing_operation():
        raise Exception("Simulated failure")

    async def successful_operation():
        return "success"

    # Open the circuit
    for _ in range(circuit_breaker.failure_threshold):
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_operation)

    # Wait for recovery timeout
    await asyncio.sleep(2.5)

    # Execute successful calls to close circuit
    for _ in range(circuit_breaker.success_threshold):
        result = await circuit_breaker.call(successful_operation)
        assert result == "success"

    # Circuit should be CLOSED
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.success_count == 0  # Reset after closing


@pytest.mark.asyncio
async def test_circuit_breaker_reopens_from_half_open_on_failure(circuit_breaker):
    """Test circuit breaker reopens from HALF_OPEN on any failure."""

    async def failing_operation():
        raise Exception("Simulated failure")

    # Open the circuit
    for _ in range(circuit_breaker.failure_threshold):
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_operation)

    # Wait for recovery timeout
    await asyncio.sleep(2.5)

    # One failure in HALF_OPEN should reopen circuit
    with pytest.raises(Exception, match="Simulated failure"):
        await circuit_breaker.call(failing_operation)

    assert circuit_breaker.state == CircuitState.OPEN


def test_circuit_breaker_manual_reset(circuit_breaker):
    """Test circuit breaker manual state reset."""
    circuit_breaker.failure_count = 5
    circuit_breaker.state = CircuitState.OPEN
    circuit_breaker.success_count = 1

    # Manually reset state
    circuit_breaker.state = CircuitState.CLOSED
    circuit_breaker.failure_count = 0
    circuit_breaker.success_count = 0

    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 0
    assert circuit_breaker.success_count == 0


# --- ResilienceConfig Tests ---


def test_resilience_config_defaults():
    """Test ResilienceConfig default values."""
    config = ResilienceConfig()

    assert config.circuit_breaker_enabled is True
    assert config.failure_threshold == 5
    assert config.recovery_timeout_seconds == 60
    assert config.success_threshold == 2
    assert config.retry_enabled is True
    assert config.max_retries == 3
    assert config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF
    assert config.initial_retry_delay_ms == 100
    assert config.max_retry_delay_ms == 10000
    assert config.fallback_enabled is True
    assert config.timeout_seconds == 30.0
    assert config.bulkhead_enabled is False
    assert config.max_concurrent_calls == 100


def test_resilience_config_custom():
    """Test ResilienceConfig with custom values."""
    config = ResilienceConfig(
        failure_threshold=10,
        retry_strategy=RetryStrategy.LINEAR_BACKOFF,
        timeout_seconds=15.0,
        bulkhead_enabled=True,
        max_concurrent_calls=50,
    )

    assert config.failure_threshold == 10
    assert config.retry_strategy == RetryStrategy.LINEAR_BACKOFF
    assert config.timeout_seconds == 15.0
    assert config.bulkhead_enabled is True
    assert config.max_concurrent_calls == 50


# --- ResilienceCapability Tests ---


def test_resilience_capability_initialization(resilience):
    """Test ResilienceCapability initialization."""
    assert resilience.name == "resilience"
    assert isinstance(resilience.config, ResilienceConfig)
    assert resilience._circuit_breakers == {}
    assert resilience._metrics["total_calls"] == 0


@pytest.mark.asyncio
async def test_execute_with_resilience_success(resilience):
    """Test successful operation execution."""

    async def successful_operation(value: int) -> int:
        return value * 2

    result = await resilience.execute_with_resilience(
        operation=successful_operation,
        operation_name="double",
        value=5,
    )

    assert result.success is True
    assert result.output["result"] == 10
    assert result.output["attempts"] == 1
    assert result.output["used_fallback"] is False


@pytest.mark.asyncio
async def test_execute_with_resilience_retry_success(resilience):
    """Test operation succeeds after retries."""
    call_count = 0

    async def flaky_operation() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary failure")
        return "success"

    result = await resilience.execute_with_resilience(
        operation=flaky_operation,
        operation_name="flaky",
    )

    assert result.success is True
    assert result.output["result"] == "success"
    assert result.output["attempts"] == 3
    assert call_count == 3


@pytest.mark.asyncio
async def test_execute_with_resilience_max_retries_exceeded(resilience):
    """Test operation fails after max retries."""
    # Disable circuit breaker for this test to focus on retries
    resilience.config.circuit_breaker_enabled = False

    async def always_failing_operation() -> str:
        raise Exception("Permanent failure")

    result = await resilience.execute_with_resilience(
        operation=always_failing_operation,
        operation_name="failing",
    )

    assert result.success is False
    assert "error" in result.output
    assert "Permanent failure" in result.output["error"]
    assert result.output["attempts"] == resilience.config.max_retries + 1


@pytest.mark.asyncio
async def test_execute_with_resilience_fallback(resilience):
    """Test fallback execution on failure."""

    async def failing_operation() -> str:
        raise Exception("Main operation failed")

    async def fallback_operation() -> str:
        return "fallback result"

    result = await resilience.execute_with_resilience(
        operation=failing_operation,
        operation_name="with_fallback",
        fallback=fallback_operation,
    )

    assert result.success is True
    assert result.output["result"] == "fallback result"
    assert result.output["used_fallback"] is True


@pytest.mark.asyncio
async def test_execute_with_resilience_no_fallback(resilience):
    """Test operation fails without fallback."""
    resilience.config.fallback_enabled = False

    async def failing_operation() -> str:
        raise Exception("Operation failed")

    result = await resilience.execute_with_resilience(
        operation=failing_operation,
        operation_name="no_fallback",
    )

    assert result.success is False
    assert "error" in result.output
    assert "used_fallback" not in result.output


@pytest.mark.asyncio
async def test_execute_with_resilience_timeout(resilience):
    """Test operation timeout protection."""
    resilience.config.timeout_seconds = 0.5
    resilience.config.max_retries = 0  # Disable retries for this test

    async def slow_operation() -> str:
        await asyncio.sleep(2.0)
        return "should timeout"

    result = await resilience.execute_with_resilience(
        operation=slow_operation,
        operation_name="slow",
    )

    assert result.success is False
    assert "timed out" in result.output["error"].lower()


@pytest.mark.asyncio
async def test_execute_with_resilience_bulkhead(resilience):
    """Test bulkhead isolation limits concurrent calls."""
    resilience.config.bulkhead_enabled = True
    resilience.config.max_concurrent_calls = 2

    async def slow_operation() -> str:
        await asyncio.sleep(0.5)
        return "completed"

    # Start 3 operations (should only allow 2 concurrent)
    tasks = [
        resilience.execute_with_resilience(
            operation=slow_operation,
            operation_name=f"op_{i}",
        )
        for i in range(3)
    ]

    results = await asyncio.gather(*tasks)

    # All should eventually complete
    assert all(r.success for r in results)
    assert all(r.output["result"] == "completed" for r in results)


@pytest.mark.asyncio
async def test_calculate_retry_delay_exponential(resilience):
    """Test exponential backoff calculation."""
    resilience.config.retry_strategy = RetryStrategy.EXPONENTIAL_BACKOFF
    resilience.config.initial_retry_delay_ms = 100
    resilience.config.max_retry_delay_ms = 10000

    # Attempt 0: 100ms
    delay_0 = resilience._calculate_retry_delay(0)
    assert delay_0 == 0.1  # 100ms = 0.1s

    # Attempt 1: 200ms
    delay_1 = resilience._calculate_retry_delay(1)
    assert delay_1 == 0.2

    # Attempt 2: 400ms
    delay_2 = resilience._calculate_retry_delay(2)
    assert delay_2 == 0.4

    # Attempt 10: should be capped at max
    delay_10 = resilience._calculate_retry_delay(10)
    assert delay_10 == 10.0  # max_retry_delay_ms


@pytest.mark.asyncio
async def test_calculate_retry_delay_linear(resilience):
    """Test linear backoff calculation."""
    resilience.config.retry_strategy = RetryStrategy.LINEAR_BACKOFF
    resilience.config.initial_retry_delay_ms = 100

    # Attempt 0: 100ms
    delay_0 = resilience._calculate_retry_delay(0)
    assert delay_0 == 0.1

    # Attempt 1: 200ms
    delay_1 = resilience._calculate_retry_delay(1)
    assert delay_1 == 0.2

    # Attempt 2: 300ms
    delay_2 = resilience._calculate_retry_delay(2)
    assert delay_2 == 0.3


@pytest.mark.asyncio
async def test_calculate_retry_delay_constant(resilience):
    """Test constant backoff calculation."""
    resilience.config.retry_strategy = RetryStrategy.CONSTANT_BACKOFF
    resilience.config.initial_retry_delay_ms = 100

    # All attempts: 100ms
    delay_0 = resilience._calculate_retry_delay(0)
    delay_1 = resilience._calculate_retry_delay(1)
    delay_2 = resilience._calculate_retry_delay(2)

    assert delay_0 == 0.1
    assert delay_1 == 0.1
    assert delay_2 == 0.1


@pytest.mark.asyncio
async def test_get_circuit_state(resilience):
    """Test get_circuit_state method."""
    result = await resilience.get_circuit_state(operation_name="test_op")

    assert result.success is True
    assert result.output["state"] == "not_initialized"


@pytest.mark.asyncio
async def test_reset_circuit(resilience):
    """Test reset_circuit method."""
    # Trigger some failures
    async def failing_operation():
        raise Exception("Failure")

    for _ in range(2):
        await resilience.execute_with_resilience(
            operation=failing_operation,
            operation_name="fail",
        )

    # Reset circuit
    result = await resilience.reset_circuit(operation_name="fail")

    assert result.success is True
    assert result.output["reset"] is True
    assert result.output["operation"] == "fail"

    # Verify state is reset
    state_result = await resilience.get_circuit_state(
        operation_name="fail"
    )
    assert state_result.output["state"] == CircuitState.CLOSED.value
    assert state_result.output["failure_count"] == 0


@pytest.mark.asyncio
async def test_get_metrics(resilience):
    """Test get_metrics method."""

    async def successful_operation():
        return "success"

    # Execute some operations
    await resilience.execute_with_resilience(
        operation=successful_operation,
        operation_name="test",
    )

    result = await resilience.get_metrics()

    assert result.success is True
    assert result.output["total_calls"] == 1
    assert result.output["successful_calls"] == 1
    assert result.output["failed_calls"] == 0
    assert result.output["retried_calls"] == 0
    assert result.output["fallback_calls"] == 0
    assert result.output["timeouts"] == 0


@pytest.mark.asyncio
async def test_reset_metrics(resilience):
    """Test reset_metrics method."""

    async def successful_operation():
        return "success"

    # Execute operations to populate metrics
    await resilience.execute_with_resilience(
        operation=successful_operation,
        operation_name="test",
    )

    # Reset metrics
    result = await resilience.reset_metrics()

    assert result.success is True
    assert result.output["metrics_reset"] is True

    # Verify metrics are reset
    metrics_result = await resilience.get_metrics()
    assert metrics_result.output["total_calls"] == 0
    assert metrics_result.output["successful_calls"] == 0


@pytest.mark.asyncio
async def test_execute_default_action(resilience):
    """Test execute with default action (get_metrics)."""
    result = await resilience.execute()

    assert result.success is True
    assert "total_calls" in result.output
    assert "successful_calls" in result.output


@pytest.mark.asyncio
async def test_execute_get_circuit_state_action(resilience):
    """Test execute with get_circuit_state action."""
    result = await resilience.execute(
        action="get_circuit_state", operation_name="test"
    )

    assert result.success is True
    assert "state" in result.output
    assert result.output["state"] == "not_initialized"


@pytest.mark.asyncio
async def test_execute_reset_circuit_action(resilience):
    """Test execute with reset_circuit action."""
    result = await resilience.execute(
        action="reset_circuit", operation_name="test"
    )

    assert result.success is True
    assert result.output["reset"] is False


@pytest.mark.asyncio
async def test_execute_reset_metrics_action(resilience):
    """Test execute with reset_metrics action."""
    result = await resilience.execute(action="reset_metrics")

    assert result.success is True
    assert result.output["metrics_reset"] is True


@pytest.mark.asyncio
async def test_full_resilience_workflow(resilience):
    """Test complete resilience workflow."""
    call_count = 0

    async def flaky_operation(value: int) -> int:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Temporary failure")
        return value * 2

    async def fallback_operation(value: int) -> int:
        return value  # Just return input

    # 1. Execute with retry and fallback
    result = await resilience.execute_with_resilience(
        operation=flaky_operation,
        operation_name="flaky",
        fallback=fallback_operation,
        value=10,
    )

    assert result.success is True
    assert result.output["result"] == 20
    assert result.output["attempts"] == 2
    assert result.output["used_fallback"] is False

    # 2. Check circuit state
    state = await resilience.get_circuit_state(operation_name="flaky")
    assert state.output["state"] == CircuitState.CLOSED.value

    # 3. Check metrics
    metrics = await resilience.get_metrics()
    assert metrics.output["total_calls"] == 1
    assert metrics.output["successful_calls"] == 1
    assert metrics.output["retried_calls"] == 1

    # 4. Reset metrics
    reset_result = await resilience.reset_metrics()
    assert reset_result.output["metrics_reset"] is True

    # 5. Verify metrics reset
    new_metrics = await resilience.get_metrics()
    assert new_metrics.output["total_calls"] == 0


@pytest.mark.asyncio
async def test_concurrent_operations(resilience):
    """Test concurrent operations through resilience."""

    async def operation(value: int) -> int:
        await asyncio.sleep(0.1)
        return value * 2

    # Execute 5 operations concurrently
    tasks = [
        resilience.execute_with_resilience(
            operation=operation,
            operation_name=f"op_{i}",
            value=i,
        )
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(r.success for r in results)
    assert [r.output["result"] for r in results] == [0, 2, 4, 6, 8]

    # Check metrics
    metrics = await resilience.get_metrics()
    assert metrics.output["total_calls"] == 5
    assert metrics.output["successful_calls"] == 5


@pytest.mark.asyncio
async def test_metrics_tracking_with_failures(resilience):
    """Test metrics tracking with various failure scenarios."""
    call_count = 0

    async def sometimes_failing_operation() -> str:
        nonlocal call_count
        call_count += 1
        if call_count % 2 == 0:
            raise Exception("Failure")
        return "success"

    async def fallback_operation() -> str:
        return "fallback"

    # Execute multiple operations
    for _ in range(4):
        await resilience.execute_with_resilience(
            operation=sometimes_failing_operation,
            operation_name="sometimes_failing",
            fallback=fallback_operation,
        )

    # Check metrics
    metrics = await resilience.get_metrics()
    assert metrics.output["total_calls"] == 4
    # Some succeed, some use fallback
    assert metrics.output["successful_calls"] + metrics.output["fallback_calls"] == 4
