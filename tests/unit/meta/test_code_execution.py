"""Unit tests for paracle_meta.capabilities.code_execution module."""

import pytest

from paracle_meta.capabilities.code_execution import (
    CodeExecutionCapability,
    CodeExecutionConfig,
    ExecutionResult,
)


class TestCodeExecutionConfig:
    """Tests for CodeExecutionConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CodeExecutionConfig()
        assert "python" in config.allowed_languages
        assert config.max_execution_time == 60.0
        assert config.max_memory_mb == 512
        assert config.allow_network is False
        assert config.allow_file_write is True
        assert config.install_packages is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CodeExecutionConfig(
            allowed_languages=["python", "javascript"],
            max_execution_time=120.0,
            max_memory_mb=1024,
            allow_network=True,
        )
        assert "javascript" in config.allowed_languages
        assert config.max_execution_time == 120.0
        assert config.max_memory_mb == 1024
        assert config.allow_network is True


class TestExecutionResult:
    """Tests for ExecutionResult."""

    def test_create_success_result(self):
        """Test creating successful execution result."""
        result = ExecutionResult(
            stdout="Hello, World!\n",
            stderr="",
            return_code=0,
            duration_ms=100.0,
            language="python",
            files_created=["output.txt"],
        )

        assert result.stdout == "Hello, World!\n"
        assert result.stderr == ""
        assert result.return_code == 0
        assert result.success is True
        assert result.language == "python"
        assert "output.txt" in result.files_created

    def test_create_failure_result(self):
        """Test creating failed execution result."""
        result = ExecutionResult(
            stdout="",
            stderr="Error: undefined variable",
            return_code=1,
            duration_ms=50.0,
            language="python",
        )

        assert result.success is False
        assert result.return_code == 1
        assert "Error" in result.stderr

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ExecutionResult(
            stdout="output",
            stderr="",
            return_code=0,
            duration_ms=75.0,
            language="python",
        )

        data = result.to_dict()

        assert data["stdout"] == "output"
        assert data["return_code"] == 0
        assert data["success"] is True
        assert data["duration_ms"] == 75.0
        assert data["language"] == "python"


class TestCodeExecutionCapability:
    """Tests for CodeExecutionCapability."""

    @pytest.fixture
    def code_capability(self):
        """Create code execution capability instance."""
        return CodeExecutionCapability()

    @pytest.fixture
    def code_capability_custom(self):
        """Create capability with custom config."""
        config = CodeExecutionConfig(
            allowed_languages=["python"],
            max_execution_time=30.0,
            allow_network=False,
        )
        return CodeExecutionCapability(config=config)

    def test_initialization(self, code_capability):
        """Test capability initialization."""
        assert code_capability.name == "code_execution"
        assert "code" in code_capability.description.lower()

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, code_capability):
        """Test initialize and shutdown lifecycle."""
        await code_capability.initialize()
        assert code_capability.is_initialized is True
        assert code_capability._temp_dir is not None
        assert code_capability._temp_dir.exists()

        await code_capability.shutdown()
        assert code_capability.is_initialized is False
        # Temp dir should be cleaned up
        assert code_capability._temp_dir is None

    @pytest.mark.asyncio
    async def test_run_simple_python(self, code_capability):
        """Test running simple Python code."""
        await code_capability.initialize()

        result = await code_capability.run_python("print('Hello, World!')")

        assert result.success is True
        assert "Hello, World!" in result.output["stdout"]
        assert result.output["return_code"] == 0

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_python_with_error(self, code_capability):
        """Test running Python code with error."""
        await code_capability.initialize()

        result = await code_capability.run_python("raise ValueError('Test error')")

        assert result.success is True  # Capability executed successfully
        # But the code itself failed
        assert result.output["return_code"] != 0
        assert "ValueError" in result.output["stderr"]

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_python_calculation(self, code_capability):
        """Test running Python calculation."""
        await code_capability.initialize()

        code = """
result = sum(range(10))
print(f"Sum: {result}")
"""
        result = await code_capability.run_python(code)

        assert result.success is True
        assert "Sum: 45" in result.output["stdout"]

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_disallowed_language(self, code_capability_custom):
        """Test running disallowed language."""
        await code_capability_custom.initialize()

        result = await code_capability_custom.execute(
            action="run",
            code="console.log('test');",
            language="javascript",
        )

        assert result.success is False
        assert "not allowed" in result.error.lower()

        await code_capability_custom.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, code_capability):
        """Test execute with unknown action."""
        await code_capability.initialize()

        result = await code_capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_analyze_code_lint(self, code_capability):
        """Test code analysis with linting."""
        await code_capability.initialize()

        code = """
def foo():
    x = 1
    return x
"""
        result = await code_capability.analyze(code, checks=["lint"])

        # Result should contain lint check results
        assert result.success is True
        assert "checks" in result.output

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_convenience_methods(self, code_capability):
        """Test convenience method wrappers."""
        await code_capability.initialize()

        # Test run_python
        result = await code_capability.run_python("print(1+1)")
        assert result.success is True

        await code_capability.shutdown()


class TestCodeExecutionSecurity:
    """Security-focused tests for CodeExecutionCapability."""

    @pytest.fixture
    def secure_capability(self):
        """Create capability with secure settings."""
        config = CodeExecutionConfig(
            allowed_languages=["python"],
            max_execution_time=10.0,
            allow_network=False,
            allow_file_write=False,
        )
        return CodeExecutionCapability(config=config)

    @pytest.mark.asyncio
    async def test_timeout_enforcement(self, secure_capability):
        """Test that timeout is enforced."""
        await secure_capability.initialize()

        # This code would run forever without timeout
        code = """
import time
while True:
    time.sleep(0.1)
"""
        result = await secure_capability.execute(
            action="run",
            code=code,
            language="python",
        )

        # Should fail due to timeout
        assert result.success is False or "timeout" in str(result.output).lower()

        await secure_capability.shutdown()

    def test_secure_config(self, secure_capability):
        """Test that secure config is applied."""
        assert secure_capability.config.allow_network is False
        assert secure_capability.config.allow_file_write is False
        assert secure_capability.config.max_execution_time == 10.0
