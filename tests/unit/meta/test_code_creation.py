"""Unit tests for paracle_meta.capabilities.code_creation module."""

import pytest
from paracle_meta.capabilities.code_creation import (
    CodeCreationCapability,
    CodeCreationConfig,
)


class TestCodeCreationConfig:
    """Tests for CodeCreationConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CodeCreationConfig()
        assert config.output_path is None
        assert config.default_language == "python"
        assert config.include_docstrings is True
        assert config.include_type_hints is True
        assert config.test_framework == "pytest"
        assert config.style_guide == "google"
        assert config.auto_save is False

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CodeCreationConfig(
            output_path="/tmp/generated",
            default_language="typescript",
            include_docstrings=False,
            test_framework="unittest",
            auto_save=True,
        )
        assert config.output_path == "/tmp/generated"
        assert config.default_language == "typescript"
        assert config.include_docstrings is False
        assert config.test_framework == "unittest"
        assert config.auto_save is True


class TestCodeCreationCapability:
    """Tests for CodeCreationCapability."""

    @pytest.fixture
    def code_capability(self, tmp_path):
        """Create code creation capability instance."""
        from paracle_meta.capabilities.filesystem import FileSystemConfig

        config = CodeCreationConfig(
            output_path=str(tmp_path),
            auto_save=False,
            filesystem_config=FileSystemConfig(
                base_path=str(tmp_path),
                allow_absolute_paths=False,
            ),
        )
        return CodeCreationCapability(config=config)

    def test_initialization(self, code_capability):
        """Test capability initialization."""
        assert code_capability.name == "code_creation"
        assert "code" in code_capability.description.lower()

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, code_capability):
        """Test initialize and shutdown lifecycle."""
        await code_capability.initialize()
        assert code_capability.is_initialized is True
        assert code_capability._anthropic is not None
        assert code_capability._filesystem is not None

        await code_capability.shutdown()
        assert code_capability.is_initialized is False

    @pytest.mark.asyncio
    async def test_create_function_mock(self, code_capability):
        """Test creating a function (mock mode)."""
        await code_capability.initialize()

        result = await code_capability.create_function(
            name="add_numbers",
            description="Add two numbers together",
        )

        assert result.success is True
        assert "code" in result.output

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_create_class_mock(self, code_capability):
        """Test creating a class (mock mode)."""
        await code_capability.initialize()

        result = await code_capability.create_class(
            name="UserService",
            description="Service for managing users",
        )

        assert result.success is True
        assert "code" in result.output

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_create_module_mock(self, code_capability):
        """Test creating a module (mock mode)."""
        await code_capability.initialize()

        result = await code_capability.create_module(
            name="authentication",
            description="Authentication module with login and logout",
        )

        assert result.success is True
        assert "code" in result.output

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_create_tests_mock(self, code_capability):
        """Test creating tests for code (mock mode)."""
        await code_capability.initialize()

        code = """
def add(a: int, b: int) -> int:
    return a + b
"""
        result = await code_capability.create_tests(
            code=code,
            test_framework="pytest",
        )

        assert result.success is True
        assert "code" in result.output

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_refactor_code_mock(self, code_capability):
        """Test refactoring code (mock mode)."""
        await code_capability.initialize()

        code = """
def get_user_data(user_id):
    # Fetch from database
    import sqlite3
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()
"""
        result = await code_capability.refactor(
            code=code,
            instructions="Extract database logic into a repository class",
        )

        assert result.success is True
        assert "code" in result.output

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_add_docstrings_mock(self, code_capability):
        """Test adding docstrings (mock mode)."""
        await code_capability.initialize()

        code = """
def calculate(x, y, operation):
    if operation == 'add':
        return x + y
    elif operation == 'subtract':
        return x - y
    else:
        raise ValueError(f"Unknown operation: {operation}")
"""
        result = await code_capability.execute(
            action="add_docstrings",
            code=code,
            style="google",
        )

        assert result.success is True
        assert "code" in result.output

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_add_type_hints_mock(self, code_capability):
        """Test adding type hints (mock mode)."""
        await code_capability.initialize()

        code = """
def process_items(items):
    results = []
    for item in items:
        results.append(item.upper())
    return results
"""
        result = await code_capability.execute(
            action="add_type_hints",
            code=code,
        )

        assert result.success is True
        assert "code" in result.output

        await code_capability.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, code_capability):
        """Test execute with unknown action."""
        await code_capability.initialize()

        result = await code_capability.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await code_capability.shutdown()


class TestCodeCreationWithFilesystem:
    """Tests for code creation with filesystem integration."""

    @pytest.fixture
    def code_capability_with_fs(self, tmp_path):
        """Create capability with filesystem enabled."""
        from paracle_meta.capabilities.filesystem import FileSystemConfig

        config = CodeCreationConfig(
            output_path=str(tmp_path),
            auto_save=True,
            filesystem_config=FileSystemConfig(
                base_path=str(tmp_path),
                allow_absolute_paths=False,
            ),
        )
        return CodeCreationCapability(config=config)

    @pytest.mark.asyncio
    async def test_create_and_save_module(self, code_capability_with_fs, tmp_path):
        """Test creating and saving a module."""
        await code_capability_with_fs.initialize()

        result = await code_capability_with_fs.create_module(
            name="utils",
            description="Utility functions",
            save_path="utils.py",
        )

        assert result.success is True

        # If auto_save is working, file should be saved
        # (depends on mock behavior)

        await code_capability_with_fs.shutdown()


class TestCodeCreationPrompts:
    """Tests for code creation prompts."""

    def test_module_prompt_format(self):
        """Test MODULE_PROMPT is properly formatted."""
        prompt = CodeCreationCapability.MODULE_PROMPT.format(
            name="test_module",
            description="A test module",
            additional_context="",
        )
        assert "test_module" in prompt
        assert "A test module" in prompt
        assert "Python 3.10+" in prompt

    def test_class_prompt_format(self):
        """Test CLASS_PROMPT is properly formatted."""
        prompt = CodeCreationCapability.CLASS_PROMPT.format(
            name="TestClass",
            description="A test class",
            base_classes="BaseModel",
            additional_context="",
        )
        assert "TestClass" in prompt
        assert "BaseModel" in prompt

    def test_function_prompt_format(self):
        """Test FUNCTION_PROMPT is properly formatted."""
        prompt = CodeCreationCapability.FUNCTION_PROMPT.format(
            name="test_func",
            description="A test function",
            parameters="x: int, y: int",
            return_type="int",
            additional_context="",
        )
        assert "test_func" in prompt
        assert "x: int" in prompt

    def test_test_prompt_format(self):
        """Test TEST_PROMPT is properly formatted."""
        prompt = CodeCreationCapability.TEST_PROMPT.format(
            code="def add(a, b): return a + b",
            test_framework="pytest",
        )
        assert "def add" in prompt
        assert "pytest" in prompt
