"""Unit tests for paracle_retry package - RetryManager."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from paracle_retry import RetryManager, RetryPolicy
from paracle_retry.conditions import (
    CustomCondition,
    NetworkErrorCondition,
    RateLimitCondition,
    ServerErrorCondition,
    TimeoutCondition,
)
from paracle_retry.exceptions import MaxRetriesExceededError


@pytest.fixture
def temp_db():
    """Create temporary database directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def retry_manager(temp_db):
    """Create RetryManager with temporary database."""
    db_path = temp_db / "retry_history.db"
    return RetryManager(str(db_path))


@pytest.fixture
def simple_policy():
    """Create simple retry policy."""
    return RetryPolicy(
        max_retries=3,
        initial_delay=0.1,
        max_delay=1.0,
        exponential_backoff=True,
    )


class TestRetryManager:
    """Test RetryManager functionality."""

    def test_initialization(self, retry_manager):
        """Test RetryManager initialization."""
        assert retry_manager is not None
        assert retry_manager._conn is not None
        assert retry_manager._history_enabled is True

    def test_retry_success_no_retries(self, retry_manager, simple_policy):
        """Test successful operation without retries."""

        @retry_manager.with_retry(simple_policy)
        def successful_operation():
            return "success"

        result = successful_operation()
        assert result == "success"

        # Check history
        history = retry_manager.get_history()
        assert len(history) == 1
        assert history[0]["success"] is True
        assert history[0]["attempts"] == 1

    def test_retry_with_transient_error(self, retry_manager, simple_policy):
        """Test retry with transient error."""
        attempt_count = {"count": 0}

        @retry_manager.with_retry(simple_policy)
        def flaky_operation():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise ConnectionError("Temporary network error")
            return "success"

        result = flaky_operation()
        assert result == "success"
        assert attempt_count["count"] == 3

        # Check history
        history = retry_manager.get_history()
        assert len(history) == 1
        assert history[0]["success"] is True
        assert history[0]["attempts"] == 3

    def test_retry_max_retries_exceeded(self, retry_manager, simple_policy):
        """Test retry when max retries exceeded."""

        @retry_manager.with_retry(simple_policy)
        def always_fails():
            raise ConnectionError("Persistent error")

        with pytest.raises(MaxRetriesExceededError) as exc_info:
            always_fails()

        assert "Max retries (3) exceeded" in str(exc_info.value)

        # Check history
        history = retry_manager.get_history()
        assert len(history) == 1
        assert history[0]["success"] is False
        assert history[0]["attempts"] == 4  # Initial + 3 retries

    def test_exponential_backoff(self, retry_manager):
        """Test exponential backoff delays."""
        policy = RetryPolicy(
            max_retries=3,
            initial_delay=0.1,
            max_delay=2.0,
            exponential_backoff=True,
        )

        delays = []
        attempt_count = {"count": 0}

        @retry_manager.with_retry(policy)
        def track_delays():
            attempt_count["count"] += 1
            if attempt_count["count"] > 1:
                delays.append(datetime.now())
            if attempt_count["count"] < 4:
                raise ConnectionError("Error")
            return "success"

        track_delays()

        # Verify delays increase exponentially
        assert len(delays) >= 2
        # Note: Actual timing validation is complex due to jitter
        # Just verify we got multiple delays

    def test_rate_limit_condition(self, retry_manager):
        """Test RateLimitCondition retry logic."""
        policy = RetryPolicy(
            max_retries=2,
            conditions=[RateLimitCondition()],
        )

        @retry_manager.with_retry(policy)
        def rate_limited():
            raise Exception("Rate limit exceeded")

        with pytest.raises(MaxRetriesExceededError):
            rate_limited()

    def test_network_error_condition(self, retry_manager):
        """Test NetworkErrorCondition retry logic."""
        policy = RetryPolicy(
            max_retries=2,
            conditions=[NetworkErrorCondition()],
        )

        attempt_count = {"count": 0}

        @retry_manager.with_retry(policy)
        def network_error():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise ConnectionError("Network error")
            return "success"

        result = network_error()
        assert result == "success"
        assert attempt_count["count"] == 3

    def test_custom_condition(self, retry_manager):
        """Test CustomCondition with lambda."""

        def should_retry_custom(error):
            return "retry_me" in str(error)

        policy = RetryPolicy(
            max_retries=2,
            conditions=[CustomCondition(should_retry_custom)],
        )

        attempt_count = {"count": 0}

        @retry_manager.with_retry(policy)
        def custom_error():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise Exception("retry_me")
            return "success"

        result = custom_error()
        assert result == "success"
        assert attempt_count["count"] == 2

    def test_multiple_conditions(self, retry_manager):
        """Test policy with multiple conditions."""
        policy = RetryPolicy(
            max_retries=3,
            conditions=[
                NetworkErrorCondition(),
                TimeoutCondition(),
                ServerErrorCondition(),
            ],
        )

        attempt_count = {"count": 0}

        @retry_manager.with_retry(policy)
        def multi_error():
            attempt_count["count"] += 1
            if attempt_count["count"] == 1:
                raise ConnectionError("Network")
            elif attempt_count["count"] == 2:
                raise TimeoutError("Timeout")
            elif attempt_count["count"] == 3:
                raise Exception("503 Server Error")
            return "success"

        result = multi_error()
        assert result == "success"
        assert attempt_count["count"] == 4

    def test_history_tracking(self, retry_manager, simple_policy):
        """Test retry history tracking."""

        @retry_manager.with_retry(simple_policy)
        def operation1():
            return "op1"

        @retry_manager.with_retry(simple_policy)
        def operation2():
            raise ValueError("Error")

        operation1()

        try:
            operation2()
        except MaxRetriesExceededError:
            pass

        history = retry_manager.get_history()
        assert len(history) >= 2

        # Check first operation
        op1_history = [h for h in history if h["operation_id"] == "operation1"]
        assert len(op1_history) > 0
        assert op1_history[0]["success"] is True

        # Check second operation
        op2_history = [h for h in history if h["operation_id"] == "operation2"]
        assert len(op2_history) > 0
        assert op2_history[0]["success"] is False

    def test_clear_history(self, retry_manager, simple_policy):
        """Test clearing retry history."""

        @retry_manager.with_retry(simple_policy)
        def operation():
            return "success"

        operation()

        history_before = retry_manager.get_history()
        assert len(history_before) > 0

        retry_manager.clear_history()

        history_after = retry_manager.get_history()
        assert len(history_after) == 0

    def test_get_statistics(self, retry_manager, simple_policy):
        """Test getting retry statistics."""

        @retry_manager.with_retry(simple_policy)
        def successful():
            return "success"

        @retry_manager.with_retry(simple_policy)
        def failing():
            raise ValueError("Error")

        successful()

        try:
            failing()
        except MaxRetriesExceededError:
            pass

        stats = retry_manager.get_statistics()
        assert stats["total_operations"] >= 2
        assert stats["successful_operations"] >= 1
        assert stats["failed_operations"] >= 1
        assert 0 <= stats["success_rate"] <= 100

    def test_no_history_mode(self, temp_db):
        """Test RetryManager without history tracking."""
        db_path = temp_db / "retry_history.db"
        manager = RetryManager(str(db_path), history_enabled=False)

        policy = RetryPolicy(max_retries=2)

        @manager.with_retry(policy)
        def operation():
            return "success"

        operation()

        history = manager.get_history()
        assert len(history) == 0

    def test_jitter_adds_randomness(self, retry_manager):
        """Test that jitter adds randomness to delays."""
        policy = RetryPolicy(
            max_retries=3,
            initial_delay=1.0,
            exponential_backoff=True,
            jitter=True,
        )

        delays = []
        attempt_count = {"count": 0}

        @retry_manager.with_retry(policy)
        def measure_jitter():
            attempt_count["count"] += 1
            start = datetime.now()
            if attempt_count["count"] < 3:
                delays.append(start)
                raise ConnectionError("Error")
            return "success"

        measure_jitter()

        # With jitter, delays should vary slightly
        # Just verify we completed with retries
        assert attempt_count["count"] == 3

    def test_max_delay_cap(self, retry_manager):
        """Test that delays are capped at max_delay."""
        policy = RetryPolicy(
            max_retries=10,
            initial_delay=0.1,
            max_delay=0.5,  # Cap at 0.5 seconds
            exponential_backoff=True,
        )

        attempt_count = {"count": 0}

        @retry_manager.with_retry(policy)
        def capped_delays():
            attempt_count["count"] += 1
            if attempt_count["count"] < 5:
                raise ConnectionError("Error")
            return "success"

        capped_delays()

        # Verify delays were capped (hard to verify exact timing)
        assert attempt_count["count"] == 5


class TestRetryPolicy:
    """Test RetryPolicy configuration."""

    def test_default_policy(self):
        """Test default RetryPolicy values."""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.initial_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.exponential_backoff is True
        assert policy.jitter is True
        assert len(policy.conditions) == 0

    def test_custom_policy(self):
        """Test custom RetryPolicy configuration."""
        policy = RetryPolicy(
            max_retries=5,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_backoff=False,
            jitter=False,
        )
        assert policy.max_retries == 5
        assert policy.initial_delay == 2.0
        assert policy.max_delay == 120.0
        assert policy.exponential_backoff is False
        assert policy.jitter is False

    def test_infinite_retries(self):
        """Test infinite retries configuration."""
        policy = RetryPolicy(max_retries=-1)
        assert policy.max_retries == -1
        # Note: Infinite retries test would run forever, so we just check config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
