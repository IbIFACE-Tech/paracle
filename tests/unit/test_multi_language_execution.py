"""Tests for multi-language code execution capability.

Tests the MultiLanguageExecutionCapability which provides
code execution in Python, JavaScript, TypeScript, Go, Rust,
Bash, Ruby, Java, C, and C++.
"""

import sys
from pathlib import Path

import pytest

from paracle_meta.capabilities.multi_language_execution import (
    BashExecutor,
    ExecutionResult,
    GoExecutor,
    JavaScriptExecutor,
    Language,
    LANGUAGE_EXTENSIONS,
    MultiLanguageConfig,
    MultiLanguageExecutionCapability,
    PythonExecutor,
    RustExecutor,
)


class TestMultiLanguageConfig:
    """Tests for MultiLanguageConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MultiLanguageConfig()

        assert "python" in config.allowed_languages
        assert "javascript" in config.allowed_languages
        assert "typescript" in config.allowed_languages
        assert "go" in config.allowed_languages
        assert "rust" in config.allowed_languages
        assert "bash" in config.allowed_languages
        assert config.max_execution_time == 60.0
        assert config.max_memory_mb == 512
        assert config.allow_network is False
        assert config.allow_file_write is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = MultiLanguageConfig(
            allowed_languages=["python", "rust"],
            max_execution_time=120.0,
            allow_network=True,
            python_path="/usr/bin/python3",
        )

        assert config.allowed_languages == ["python", "rust"]
        assert config.max_execution_time == 120.0
        assert config.allow_network is True
        assert config.python_path == "/usr/bin/python3"


class TestExecutionResult:
    """Tests for ExecutionResult."""

    def test_success_result(self):
        """Test successful execution result."""
        result = ExecutionResult(
            stdout="Hello World\n",
            stderr="",
            return_code=0,
            duration_ms=50.0,
            language="python",
        )

        assert result.success is True
        assert result.stdout == "Hello World\n"
        assert result.return_code == 0
        assert result.language == "python"

    def test_failure_result(self):
        """Test failed execution result."""
        result = ExecutionResult(
            stdout="",
            stderr="Error: undefined variable",
            return_code=1,
            duration_ms=10.0,
            language="javascript",
        )

        assert result.success is False
        assert result.return_code == 1
        assert "undefined variable" in result.stderr

    def test_compile_output(self):
        """Test result with compile output."""
        result = ExecutionResult(
            stdout="42",
            stderr="",
            return_code=0,
            duration_ms=200.0,
            language="rust",
            compile_output="Compiling main.rs",
        )

        result_dict = result.to_dict()
        assert result_dict["compile_output"] == "Compiling main.rs"
        assert result_dict["success"] is True

    def test_files_created(self):
        """Test result with created files."""
        result = ExecutionResult(
            stdout="",
            stderr="",
            return_code=0,
            duration_ms=100.0,
            language="python",
            files_created=["output.txt", "data.json"],
        )

        assert result.files_created == ["output.txt", "data.json"]


class TestLanguageExtensions:
    """Tests for language file extensions."""

    def test_all_languages_have_extensions(self):
        """Test all languages have file extensions."""
        for lang in Language:
            assert lang in LANGUAGE_EXTENSIONS
            assert LANGUAGE_EXTENSIONS[lang].startswith(".")

    def test_specific_extensions(self):
        """Test specific language extensions."""
        assert LANGUAGE_EXTENSIONS[Language.PYTHON] == ".py"
        assert LANGUAGE_EXTENSIONS[Language.JAVASCRIPT] == ".js"
        assert LANGUAGE_EXTENSIONS[Language.TYPESCRIPT] == ".ts"
        assert LANGUAGE_EXTENSIONS[Language.GO] == ".go"
        assert LANGUAGE_EXTENSIONS[Language.RUST] == ".rs"
        assert LANGUAGE_EXTENSIONS[Language.JAVA] == ".java"
        assert LANGUAGE_EXTENSIONS[Language.C] == ".c"
        assert LANGUAGE_EXTENSIONS[Language.CPP] == ".cpp"


class TestPythonExecutor:
    """Tests for Python executor."""

    @pytest.fixture
    def config(self):
        return MultiLanguageConfig()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    def test_is_available(self, config, temp_dir):
        """Test Python is always available."""
        executor = PythonExecutor(config, temp_dir)
        assert executor.is_available() is True

    def test_runtime_path(self, config, temp_dir):
        """Test runtime path is sys.executable."""
        executor = PythonExecutor(config, temp_dir)
        assert executor.get_runtime_path() == sys.executable

    @pytest.mark.asyncio
    async def test_execute_simple(self, config, temp_dir):
        """Test simple Python execution."""
        executor = PythonExecutor(config, temp_dir)
        result = await executor.execute(code="print('Hello')")

        assert result.success is True
        assert "Hello" in result.stdout
        assert result.language == "python"

    @pytest.mark.asyncio
    async def test_execute_with_args(self, config, temp_dir):
        """Test execution with command line args."""
        executor = PythonExecutor(config, temp_dir)
        code = """
import sys
print(f"Args: {sys.argv[1:]}")
"""
        result = await executor.execute(code=code, args=["--test", "value"])

        assert result.success is True
        assert "test" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_error(self, config, temp_dir):
        """Test execution with error."""
        executor = PythonExecutor(config, temp_dir)
        result = await executor.execute(code="raise ValueError('test error')")

        assert result.success is False
        assert result.return_code != 0
        assert "ValueError" in result.stderr


class TestMultiLanguageCapability:
    """Tests for MultiLanguageExecutionCapability."""

    @pytest.fixture
    def config(self):
        return MultiLanguageConfig()

    @pytest.fixture
    def capability(self, config):
        return MultiLanguageExecutionCapability(config)

    def test_init(self, capability):
        """Test capability initialization."""
        assert capability.name == "multi_language_execution"
        assert (
            "Python" in capability.description
            or "python" in capability.description.lower()
        )

    @pytest.mark.asyncio
    async def test_initialize(self, capability):
        """Test capability initialization."""
        await capability.initialize()

        assert capability._initialized is True
        assert capability._temp_dir is not None
        assert capability._temp_dir.exists()
        assert "python" in capability._executors

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown(self, capability):
        """Test capability shutdown."""
        await capability.initialize()

        await capability.shutdown()

        assert capability._initialized is False
        assert capability._temp_dir is None
        assert capability._executors == {}

    @pytest.mark.asyncio
    async def test_run_python(self, capability):
        """Test running Python code."""
        await capability.initialize()

        result = await capability.run_python("print('Hello Python')")

        assert result.success is True
        assert "Hello Python" in result.output["stdout"]

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_list_languages(self, capability):
        """Test listing available languages."""
        await capability.initialize()

        result = await capability.execute(action="list_languages")

        assert result.success is True
        assert "python" in result.output
        assert result.output["python"]["available"] is True

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_check_runtime(self, capability):
        """Test checking runtime availability."""
        await capability.initialize()

        result = await capability.execute(action="check_runtime", language="python")

        assert result.success is True
        assert result.output["language"] == "python"
        assert result.output["available"] is True

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, capability):
        """Test unknown action error."""
        await capability.initialize()

        result = await capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_language_not_allowed(self, capability):
        """Test running disallowed language."""
        capability.config.allowed_languages = ["python"]
        await capability.initialize()

        result = await capability.run("console.log('test')", language="javascript")

        assert result.success is False
        assert "not allowed" in result.error

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_get_available_languages(self, capability):
        """Test getting available languages."""
        await capability.initialize()

        available = capability.get_available_languages()

        assert isinstance(available, list)
        assert "python" in available

        await capability.shutdown()


class TestJavaScriptExecutor:
    """Tests for JavaScript executor."""

    @pytest.fixture
    def config(self):
        return MultiLanguageConfig()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    def test_runtime_detection(self, config, temp_dir):
        """Test JavaScript runtime detection."""
        executor = JavaScriptExecutor(config, temp_dir)
        # Just check it doesn't raise
        available = executor.is_available()
        assert isinstance(available, bool)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not any(Path(p).exists() for p in ["/usr/bin/node", "/usr/local/bin/node"])
        and sys.platform != "win32",
        reason="Node.js not installed",
    )
    async def test_execute_if_available(self, config, temp_dir):
        """Test JavaScript execution if runtime available."""
        executor = JavaScriptExecutor(config, temp_dir)
        if executor.is_available():
            result = await executor.execute(code="console.log('Hello JS')")
            assert result.language == "javascript"


class TestGoExecutor:
    """Tests for Go executor."""

    @pytest.fixture
    def config(self):
        return MultiLanguageConfig()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    def test_runtime_detection(self, config, temp_dir):
        """Test Go runtime detection."""
        executor = GoExecutor(config, temp_dir)
        available = executor.is_available()
        assert isinstance(available, bool)


class TestRustExecutor:
    """Tests for Rust executor."""

    @pytest.fixture
    def config(self):
        return MultiLanguageConfig()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    def test_runtime_detection(self, config, temp_dir):
        """Test Rust runtime detection."""
        executor = RustExecutor(config, temp_dir)
        available = executor.is_available()
        assert isinstance(available, bool)


class TestBashExecutor:
    """Tests for Bash executor."""

    @pytest.fixture
    def config(self):
        return MultiLanguageConfig()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.platform == "win32", reason="Bash may not be available on Windows"
    )
    async def test_execute_simple(self, config, temp_dir):
        """Test simple Bash execution."""
        executor = BashExecutor(config, temp_dir)
        if executor.is_available():
            result = await executor.execute(code='echo "Hello Bash"')
            assert result.success is True
            assert "Hello Bash" in result.stdout


class TestConvenienceMethods:
    """Tests for convenience methods."""

    @pytest.fixture
    def capability(self):
        return MultiLanguageExecutionCapability()

    @pytest.mark.asyncio
    async def test_run_python_convenience(self, capability):
        """Test run_python convenience method."""
        await capability.initialize()

        result = await capability.run_python("print(1 + 1)")

        assert result.success is True
        assert "2" in result.output["stdout"]

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_with_env(self, capability):
        """Test run with environment variables."""
        await capability.initialize()

        code = """
import os
print(os.environ.get('TEST_VAR', 'not set'))
"""
        result = await capability.run(
            code,
            language="python",
            env={"TEST_VAR": "hello_env"},
        )

        assert result.success is True
        assert "hello_env" in result.output["stdout"]

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_run_with_timeout(self, capability):
        """Test run with custom timeout."""
        await capability.initialize()

        # This should complete quickly
        result = await capability.run(
            "print('fast')",
            language="python",
            timeout=5.0,
        )

        assert result.success is True

        await capability.shutdown()


class TestIntegrationWithCapabilityResult:
    """Tests for integration with CapabilityResult."""

    @pytest.fixture
    def capability(self):
        return MultiLanguageExecutionCapability()

    @pytest.mark.asyncio
    async def test_result_has_duration(self, capability):
        """Test result includes duration."""
        await capability.initialize()

        result = await capability.run_python("print('test')")

        assert result.duration_ms is not None
        assert result.duration_ms > 0

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_result_has_action(self, capability):
        """Test result includes action."""
        await capability.initialize()

        result = await capability.execute(action="list_languages")

        assert "list_languages" in str(result)

        await capability.shutdown()


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def capability(self):
        return MultiLanguageExecutionCapability()

    @pytest.mark.asyncio
    async def test_syntax_error(self, capability):
        """Test handling syntax errors."""
        await capability.initialize()

        result = await capability.run_python("print('unclosed")

        # The capability call succeeds, but the code execution fails
        assert result.success is True  # Capability worked
        assert result.output["success"] is False  # Code failed
        assert "SyntaxError" in result.output.get("stderr", "")

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_runtime_error(self, capability):
        """Test handling runtime errors."""
        await capability.initialize()

        result = await capability.run_python("x = 1 / 0")

        # The capability call succeeds, but the code execution fails
        assert result.success is True  # Capability worked
        assert result.output["success"] is False  # Code failed
        assert "ZeroDivisionError" in result.output.get("stderr", "")

        await capability.shutdown()

    @pytest.mark.asyncio
    async def test_unknown_language(self, capability):
        """Test handling unknown language."""
        await capability.initialize()

        result = await capability.run("code", language="fortran")

        assert result.success is False
        assert "not allowed" in result.error or "not available" in result.error

        await capability.shutdown()
