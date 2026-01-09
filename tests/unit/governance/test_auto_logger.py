"""Unit tests for automatic governance logging."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from paracle_core.governance import (
    agent_operation,
    async_agent_operation,
    log_agent_action,
    sanitize_args,
)
from paracle_core.governance.types import GovernanceActionType


class TestSanitizeArgs:
    """Tests for argument sanitization."""

    def test_sanitize_password(self):
        """Test that password fields are redacted."""
        args = {"username": "admin", "password": "secret123"}
        sanitized = sanitize_args(args)
        assert sanitized["username"] == "admin"
        assert sanitized["password"] == "***REDACTED***"

    def test_sanitize_token(self):
        """Test that token fields are redacted."""
        args = {"api_token": "sk-12345", "data": "public"}
        sanitized = sanitize_args(args)
        assert sanitized["api_token"] == "***REDACTED***"
        assert sanitized["data"] == "public"

    def test_sanitize_secret(self):
        """Test that secret fields are redacted."""
        args = {"api_key": "abc123", "api_secret": "xyz789"}
        sanitized = sanitize_args(args)
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["api_secret"] == "***REDACTED***"

    def test_size_limit(self):
        """Test that large values are truncated."""
        args = {"data": "x" * 300}
        sanitized = sanitize_args(args)
        assert len(sanitized["data"]) == 203  # 200 + "..."
        assert sanitized["data"].endswith("...")

    def test_nested_sanitization(self):
        """Test sanitization of nested dictionaries."""
        args = {
            "config": {
                "password": "secret",
                "username": "admin",
            }
        }
        sanitized = sanitize_args(args)
        assert sanitized["config"]["password"] == "***REDACTED***"
        assert sanitized["config"]["username"] == "admin"


class TestLogAgentAction:
    """Tests for @log_agent_action decorator."""

    @pytest.fixture
    def mock_logger(self):
        """Mock governance logger."""
        with patch("paracle_core.governance.auto_logger.logger") as mock:
            yield mock

    def test_decorator_sync_success(self, mock_logger):
        """Test decorator logs successful sync function."""

        @log_agent_action("TestAgent", GovernanceActionType.IMPLEMENTATION)
        def test_function(x: int, y: int) -> int:
            return x + y

        result = test_function(2, 3)

        assert result == 5
        # Verify logging occurred
        assert mock_logger.log_action.call_count >= 1

    @pytest.mark.asyncio
    async def test_decorator_async_success(self, mock_logger):
        """Test decorator logs successful async function."""

        @log_agent_action("TestAgent", GovernanceActionType.IMPLEMENTATION)
        async def test_function(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2

        result = await test_function(5)

        assert result == 10
        assert mock_logger.log_action.call_count >= 1

    def test_decorator_with_exception(self, mock_logger):
        """Test decorator logs failures."""

        @log_agent_action("TestAgent", GovernanceActionType.IMPLEMENTATION)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Verify failure was logged
        assert mock_logger.log_action.call_count >= 1

    @pytest.mark.asyncio
    async def test_decorator_async_with_exception(self, mock_logger):
        """Test decorator logs async failures."""

        @log_agent_action("TestAgent", GovernanceActionType.IMPLEMENTATION)
        async def failing_function():
            await asyncio.sleep(0.01)
            raise RuntimeError("Async error")

        with pytest.raises(RuntimeError, match="Async error"):
            await failing_function()

        assert mock_logger.log_action.call_count >= 1

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @log_agent_action("TestAgent", GovernanceActionType.TEST)
        def documented_function(x: int) -> int:
            """This is a test function."""
            return x

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."

    def test_inferred_action_type(self, mock_logger):
        """Test that action type is inferred from function name."""

        @log_agent_action("TestAgent")
        def implement_feature():
            return "implemented"

        result = implement_feature()
        assert result == "implemented"


class TestAgentOperation:
    """Tests for agent_operation context manager."""

    @pytest.fixture
    def mock_logger(self):
        """Mock governance logger."""
        with patch("paracle_core.governance.auto_logger.logger") as mock:
            yield mock

    def test_context_manager_success(self, mock_logger):
        """Test context manager logs operation."""
        with agent_operation(
            "TestAgent",
            GovernanceActionType.IMPLEMENTATION,
            description="Test operation",
        ):
            result = 2 + 2

        assert result == 4
        # Verify start and completion logged
        assert mock_logger.log_action.call_count >= 2

    def test_context_manager_with_exception(self, mock_logger):
        """Test context manager logs failures."""
        with pytest.raises(ValueError, match="Test error"):
            with agent_operation(
                "TestAgent",
                GovernanceActionType.TEST,
                description="Failing operation",
            ):
                raise ValueError("Test error")

        # Verify failure was logged
        assert mock_logger.log_action.call_count >= 2


class TestAsyncAgentOperation:
    """Tests for async_agent_operation context manager."""

    @pytest.fixture
    def mock_logger(self):
        """Mock governance logger."""
        with patch("paracle_core.governance.auto_logger.logger") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_async_context_manager_success(self, mock_logger):
        """Test async context manager logs operation."""
        async with async_agent_operation(
            "TestAgent",
            GovernanceActionType.IMPLEMENTATION,
            description="Async operation",
        ):
            await asyncio.sleep(0.01)
            result = 10 * 2

        assert result == 20
        assert mock_logger.log_action.call_count >= 2

    @pytest.mark.asyncio
    async def test_async_context_manager_with_exception(self, mock_logger):
        """Test async context manager logs failures."""
        with pytest.raises(RuntimeError, match="Async error"):
            async with async_agent_operation(
                "TestAgent",
                GovernanceActionType.TEST,
                description="Failing async operation",
            ):
                await asyncio.sleep(0.01)
                raise RuntimeError("Async error")

        assert mock_logger.log_action.call_count >= 2


class TestIntegration:
    """Integration tests with real logger."""

    @pytest.fixture
    def temp_parac(self):
        """Create temporary .parac structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parac_dir = Path(tmpdir) / ".parac"
            logs_dir = parac_dir / "memory" / "logs"
            logs_dir.mkdir(parents=True)

            yield parac_dir

    def test_decorator_writes_to_log(self, temp_parac, monkeypatch):
        """Test that decorator actually writes to log file."""
        # Set up environment
        monkeypatch.chdir(temp_parac.parent)

        from paracle_core.governance.logger import GovernanceLogger

        # Create logger
        logger = GovernanceLogger(parac_root=temp_parac)

        with patch("paracle_core.governance.auto_logger.logger", logger):

            @log_agent_action("IntegrationTest", GovernanceActionType.TEST)
            def test_function():
                return "success"

            result = test_function()

        assert result == "success"

        # Verify log file was created and written
        log_file = temp_parac / "memory" / "logs" / "agent_actions.log"
        assert log_file.exists()

        content = log_file.read_text()
        assert "IntegrationTest" in content
        assert "TEST" in content
        assert "test_function" in content

    @pytest.mark.asyncio
    async def test_async_decorator_writes_to_log(self, temp_parac, monkeypatch):
        """Test that async decorator writes to log file."""
        monkeypatch.chdir(temp_parac.parent)

        from paracle_core.governance.logger import GovernanceLogger

        logger = GovernanceLogger(parac_root=temp_parac)

        with patch("paracle_core.governance.auto_logger.logger", logger):

            @log_agent_action(
                "AsyncIntegrationTest", GovernanceActionType.IMPLEMENTATION
            )
            async def async_test_function():
                await asyncio.sleep(0.01)
                return "async success"

            result = await async_test_function()

        assert result == "async success"

        log_file = temp_parac / "memory" / "logs" / "agent_actions.log"
        assert log_file.exists()

        content = log_file.read_text()
        assert "AsyncIntegrationTest" in content
        assert "IMPLEMENTATION" in content


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.fixture
    def mock_logger(self):
        """Mock governance logger that raises exceptions."""
        with patch("paracle_core.governance.auto_logger.logger") as mock:
            # Make logger raise exception
            mock.log_action.side_effect = Exception("Logger failed")
            yield mock

    def test_decorator_handles_logger_failure(self, mock_logger):
        """Test that decorator doesn't break if logger fails."""

        @log_agent_action("TestAgent", GovernanceActionType.TEST)
        def test_function():
            return "still works"

        # Should not raise exception even though logger fails
        result = test_function()
        assert result == "still works"

    @pytest.mark.asyncio
    async def test_async_decorator_handles_logger_failure(self, mock_logger):
        """Test async decorator handles logger failures."""

        @log_agent_action("TestAgent", GovernanceActionType.TEST)
        async def test_function():
            await asyncio.sleep(0.01)
            return "async still works"

        result = await test_function()
        assert result == "async still works"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
