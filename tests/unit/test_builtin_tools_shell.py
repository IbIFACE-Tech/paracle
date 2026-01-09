"""Tests for built-in shell tools."""

import pytest

from paracle_tools.builtin.shell import RunCommandTool


class TestRunCommandTool:
    """Test run_command tool."""

    @pytest.mark.asyncio
    async def test_run_simple_command(self):
        # Arrange
        tool = RunCommandTool(allowed_commands=["echo"])

        # Act
        result = await tool.execute(command="echo hello")

        # Assert
        assert result.success is True
        assert "hello" in result.output["stdout"].lower()
        assert result.output["return_code"] == 0
        assert result.output["success"] is True

    @pytest.mark.asyncio
    async def test_run_command_with_args(self):
        # Arrange
        tool = RunCommandTool(allowed_commands=["python"])

        # Act
        result = await tool.execute(command="python --version")

        # Assert
        assert result.success is True
        assert result.output["return_code"] == 0
        stdout_lower = result.output["stdout"].lower()
        stderr_lower = result.output["stderr"].lower()
        assert "python" in stdout_lower or "python" in stderr_lower

    @pytest.mark.asyncio
    async def test_blocked_command_rejected(self):
        # Arrange - Only allow safe commands
        tool = RunCommandTool(allowed_commands=["echo", "ls"])

        # Act - Try to run a command NOT in the allowlist
        result = await tool.execute(command="rm -rf /")

        # Assert
        assert result.success is False
        assert "not in allowed commands" in result.error.lower()

    @pytest.mark.asyncio
    async def test_command_not_in_whitelist_rejected(self):
        # Arrange
        tool = RunCommandTool(allowed_commands=["echo", "ls"])

        # Act
        result = await tool.execute(command="python --version")

        # Assert
        assert result.success is False
        assert "not in allowed commands" in result.error.lower()

    @pytest.mark.asyncio
    async def test_command_in_whitelist_allowed(self):
        # Arrange
        tool = RunCommandTool(allowed_commands=["echo"])

        # Act
        result = await tool.execute(command="echo test")

        # Assert
        assert result.success is True
        assert "test" in result.output["stdout"]

    @pytest.mark.asyncio
    async def test_command_timeout(self):
        # Arrange
        import sys

        tool = RunCommandTool(allowed_commands=["python", "sleep"], timeout=0.1)

        # Act - Command that sleeps longer than timeout
        if sys.platform == "win32":
            cmd = 'python -c "import time; time.sleep(5)"'
        else:
            cmd = "sleep 5"
        result = await tool.execute(command=cmd)

        # Assert
        assert result.success is False
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_nonexistent_command(self):
        # Arrange
        tool = RunCommandTool(allowed_commands=["nonexistentcommand12345"])

        # Act
        result = await tool.execute(command="nonexistentcommand12345")

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_command_with_stderr(self):
        # Arrange
        tool = RunCommandTool(allowed_commands=["python"])

        # Act - Python command that writes to stderr
        cmd = "python -c \"import sys; sys.stderr.write('error message')\""
        result = await tool.execute(command=cmd)

        # Assert
        assert result.success is True  # Command runs successfully
        assert "error message" in result.output["stderr"]

    @pytest.mark.asyncio
    async def test_command_with_non_zero_exit(self):
        # Arrange
        tool = RunCommandTool(allowed_commands=["python"])

        # Act - Python command that exits with error code
        result = await tool.execute(command='python -c "import sys; sys.exit(1)"')

        # Assert
        assert result.success is True  # Tool executes successfully
        assert result.output["return_code"] == 1
        assert result.output["success"] is False  # Command itself failed
