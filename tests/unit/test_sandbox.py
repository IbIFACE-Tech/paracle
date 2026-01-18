"""Unit tests for paracle_sandbox package."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from paracle_sandbox import (
    SandboxConfig,
    SandboxExecutor,
    SandboxManager,
)
from paracle_sandbox.exceptions import (
    SandboxCreationError,
    SandboxError,
    SandboxTimeoutError,
)


class TestSandboxConfig:
    """Tests for SandboxConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = SandboxConfig()
        assert config.base_image == "paracle/sandbox:latest"
        assert config.cpu_cores == 1.0
        assert config.memory_mb == 512
        assert config.disk_mb == 1024
        assert config.timeout_seconds == 300
        assert config.network_mode == "none"
        assert config.read_only_filesystem is True
        assert config.drop_capabilities is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = SandboxConfig(
            base_image="custom:latest",
            cpu_cores=2.0,
            memory_mb=1024,
            network_mode="bridge",
        )
        assert config.base_image == "custom:latest"
        assert config.cpu_cores == 2.0
        assert config.memory_mb == 1024
        assert config.network_mode == "bridge"

    def test_validation_cpu_cores(self):
        """Test CPU cores validation."""
        with pytest.raises(ValueError):
            SandboxConfig(cpu_cores=0.05)  # Below minimum
        with pytest.raises(ValueError):
            SandboxConfig(cpu_cores=20.0)  # Above maximum

    def test_validation_memory(self):
        """Test memory validation."""
        with pytest.raises(ValueError):
            SandboxConfig(memory_mb=64)  # Below minimum
        with pytest.raises(ValueError):
            SandboxConfig(memory_mb=20000)  # Above maximum


@pytest.mark.asyncio
class TestDockerSandbox:
    """Tests for DockerSandbox."""

    @patch("docker.from_env")
    async def test_sandbox_creation(self, mock_docker):
        """Test sandbox container creation."""
        from paracle_sandbox import DockerSandbox

        # Mock Docker client
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        config = SandboxConfig()
        sandbox = DockerSandbox("test-123", config)

        await sandbox.start()

        assert sandbox.container is not None
        mock_client.containers.create.assert_called_once()
        mock_container.start.assert_called_once()

    @patch("docker.from_env")
    async def test_sandbox_execution(self, mock_docker):
        """Test command execution in sandbox."""
        from paracle_sandbox import DockerSandbox

        # Mock Docker client and container
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = (b"Hello from sandbox\n", b"")
        mock_container.exec_run.return_value = mock_exec_result
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        config = SandboxConfig(timeout_seconds=10)
        sandbox = DockerSandbox("test-123", config)

        await sandbox.start()
        result = await sandbox.execute("echo 'Hello from sandbox'")

        assert result["exit_code"] == 0
        assert "Hello from sandbox" in result["stdout"]
        assert result["timed_out"] is False

    @patch("docker.from_env")
    async def test_sandbox_timeout(self, mock_docker):
        """Test execution timeout."""
        from paracle_sandbox import DockerSandbox

        # Mock Docker client
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        # Mock exec that never completes
        mock_exec_result = MagicMock()
        mock_exec_result.exit_code = None  # Still running
        mock_container.exec_run.return_value = mock_exec_result

        config = SandboxConfig(timeout_seconds=1)
        sandbox = DockerSandbox("test-123", config)

        await sandbox.start()

        with pytest.raises(SandboxTimeoutError):
            await sandbox.execute("sleep 100", timeout=1)

        mock_container.kill.assert_called_once()

    @patch("docker.from_env")
    async def test_sandbox_stop(self, mock_docker):
        """Test sandbox cleanup."""
        from paracle_sandbox import DockerSandbox

        # Mock Docker client
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        config = SandboxConfig()
        sandbox = DockerSandbox("test-123", config)

        await sandbox.start()
        await sandbox.stop()

        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
        assert sandbox.container is None

    @patch("docker.from_env")
    async def test_image_pull(self, mock_docker):
        """Test Docker image pulling."""
        from paracle_sandbox import DockerSandbox

        from docker.errors import ImageNotFound

        # Mock Docker client
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.side_effect = ImageNotFound("Image not found")
        mock_client.images.pull.return_value = MagicMock()
        mock_docker.return_value = mock_client

        config = SandboxConfig(base_image="custom/image:v1.0")
        sandbox = DockerSandbox("test-123", config)

        await sandbox.start()

        mock_client.images.pull.assert_called_once_with("custom/image:v1.0")


@pytest.mark.asyncio
class TestSandboxManager:
    """Tests for SandboxManager."""

    @patch("docker.from_env")
    async def test_manager_create_sandbox(self, mock_docker):
        """Test sandbox creation via manager."""
        # Mock Docker
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        manager = SandboxManager(max_concurrent=5)
        config = SandboxConfig()

        sandbox = await manager.create(config)

        assert sandbox.sandbox_id in manager.active_sandboxes
        assert len(manager.active_sandboxes) == 1

    @patch("docker.from_env")
    async def test_manager_concurrent_limit(self, mock_docker):
        """Test concurrent sandbox limit."""
        # Mock Docker
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        manager = SandboxManager(max_concurrent=2)
        config = SandboxConfig()

        # Create max sandboxes
        sandbox1 = await manager.create(config)
        sandbox2 = await manager.create(config)

        # Should fail on third
        with pytest.raises(SandboxError):
            await manager.create(config)

        # Cleanup
        await manager.destroy(sandbox1.sandbox_id)
        await manager.destroy(sandbox2.sandbox_id)

    @patch("docker.from_env")
    async def test_manager_destroy_sandbox(self, mock_docker):
        """Test sandbox destruction."""
        # Mock Docker
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        manager = SandboxManager()
        config = SandboxConfig()

        sandbox = await manager.create(config)
        sandbox_id = sandbox.sandbox_id

        await manager.destroy(sandbox_id)

        assert sandbox_id not in manager.active_sandboxes

    @patch("docker.from_env")
    async def test_manager_context_manager(self, mock_docker):
        """Test managed sandbox context manager."""
        # Mock Docker
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = (b"OK\n", b"")
        mock_container.exec_run.return_value = mock_exec_result
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        manager = SandboxManager()
        config = SandboxConfig()

        sandbox_id = None
        async with manager.managed_sandbox(config) as sandbox:
            sandbox_id = sandbox.sandbox_id
            assert sandbox_id in manager.active_sandboxes

        # Should be destroyed after context
        assert sandbox_id not in manager.active_sandboxes


@pytest.mark.asyncio
class TestSandboxExecutor:
    """Tests for SandboxExecutor."""

    @patch("docker.from_env")
    async def test_executor_execute_agent(self, mock_docker):
        """Test agent execution via executor."""
        # Mock Docker
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = (b"Agent output\n", b"")
        mock_container.exec_run.return_value = mock_exec_result
        mock_container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000},
                "system_cpu_usage": 10000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900},
                "system_cpu_usage": 9000,
            },
            "memory_stats": {"usage": 104857600, "limit": 536870912},
        }
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        executor = SandboxExecutor()

        result = await executor.execute_agent(
            agent_code="print('Hello from agent')",
            config=SandboxConfig(),
            monitor=False,
        )

        assert result["success"] is True
        assert result["result"]["exit_code"] == 0
        assert "stats" in result

    @patch("docker.from_env")
    async def test_executor_with_inputs(self, mock_docker):
        """Test agent execution with inputs."""
        # Mock Docker
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = (b"42\n", b"")
        mock_container.exec_run.return_value = mock_exec_result
        mock_container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000},
                "system_cpu_usage": 10000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900},
                "system_cpu_usage": 9000,
            },
            "memory_stats": {"usage": 104857600, "limit": 536870912},
        }
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        executor = SandboxExecutor()

        agent_code = """
import json
with open('/workspace/inputs.json') as f:
    inputs = json.load(f)
print(inputs['value'])
"""

        result = await executor.execute_agent(
            agent_code=agent_code,
            inputs={"value": 42},
            monitor=False,
        )

        assert result["success"] is True

    @patch("docker.from_env")
    async def test_executor_error_handling(self, mock_docker):
        """Test error handling in executor."""
        # Mock Docker with failing execution
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.exit_code = 1
        mock_exec_result.output = (b"", b"Error: division by zero\n")
        mock_container.exec_run.return_value = mock_exec_result
        mock_container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000},
                "system_cpu_usage": 10000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900},
                "system_cpu_usage": 9000,
            },
            "memory_stats": {"usage": 104857600, "limit": 536870912},
        }
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        executor = SandboxExecutor()

        result = await executor.execute_agent(
            agent_code="1/0",  # Will cause error
            monitor=False,
        )

        assert result["success"] is False
        assert "error" in result

    @patch("docker.from_env")
    async def test_executor_batch_execution(self, mock_docker):
        """Test batch execution."""
        # Mock Docker
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = (b"OK\n", b"")
        mock_container.exec_run.return_value = mock_exec_result
        mock_container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000},
                "system_cpu_usage": 10000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900},
                "system_cpu_usage": 9000,
            },
            "memory_stats": {"usage": 104857600, "limit": 536870912},
        }
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        executor = SandboxExecutor()

        jobs = [
            {"agent_code": "print('Job 1')", "inputs": {"id": 1}, "monitor": False},
            {"agent_code": "print('Job 2')", "inputs": {"id": 2}, "monitor": False},
            {"agent_code": "print('Job 3')", "inputs": {"id": 3}, "monitor": False},
        ]

        results = await executor.execute_batch(jobs, max_concurrent=2)

        assert len(results) == 3
        assert all(r["success"] for r in results)


@pytest.mark.asyncio
class TestSandboxMonitor:
    """Tests for SandboxMonitor."""

    @patch("docker.from_env")
    async def test_monitor_start_stop(self, mock_docker):
        """Test monitor start and stop."""
        from paracle_sandbox import DockerSandbox, SandboxMonitor

        # Mock Docker
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000},
                "system_cpu_usage": 10000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900},
                "system_cpu_usage": 9000,
            },
            "memory_stats": {"usage": 104857600, "limit": 536870912},
        }
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        config = SandboxConfig()
        sandbox = DockerSandbox("test-123", config)
        await sandbox.start()

        monitor = SandboxMonitor(sandbox, interval_seconds=0.1)
        await monitor.start()

        # Let it collect some stats
        await asyncio.sleep(0.3)

        await monitor.stop()

        history = monitor.get_history()
        assert len(history) > 0

    @patch("docker.from_env")
    async def test_monitor_averages(self, mock_docker):
        """Test average calculations."""
        from paracle_sandbox import DockerSandbox, SandboxMonitor

        # Mock Docker
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000},
                "system_cpu_usage": 10000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900},
                "system_cpu_usage": 9000,
            },
            "memory_stats": {"usage": 104857600, "limit": 536870912},
        }
        mock_client.containers.create.return_value = mock_container
        mock_client.images.get.return_value = MagicMock()
        mock_docker.return_value = mock_client

        config = SandboxConfig()
        sandbox = DockerSandbox("test-123", config)
        await sandbox.start()

        monitor = SandboxMonitor(sandbox, interval_seconds=0.1)

        async with monitor:
            await asyncio.sleep(0.3)

        averages = monitor.get_averages()
        assert "cpu_percent" in averages
        assert "memory_percent" in averages
        assert averages["cpu_percent"] >= 0


def test_exception_hierarchy():
    """Test exception inheritance."""
    from paracle_sandbox.exceptions import (
        ResourceLimitError,
        SandboxError,
        SandboxExecutionError,
        SandboxTimeoutError,
    )

    # All should inherit from SandboxError
    assert issubclass(SandboxCreationError, SandboxError)
    assert issubclass(SandboxExecutionError, SandboxError)
    assert issubclass(ResourceLimitError, SandboxError)
    assert issubclass(SandboxTimeoutError, SandboxError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
