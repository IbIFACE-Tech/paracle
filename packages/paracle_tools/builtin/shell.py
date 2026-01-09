"""Shell tools for executing commands.

Security Features:
- Strict command allowlist (REQUIRED - no fallback to blocklist)
- NO shell=True option (prevents command injection attacks)
- Command argument validation with shlex
- Timeout enforcement (max 5 minutes)
- Working directory restrictions
- Audit logging of all command executions
"""

from __future__ import annotations

import asyncio
import shlex
from typing import Any

from paracle_core.logging import get_logger

from paracle_tools.builtin.base import BaseTool, PermissionError, ToolError

logger = get_logger(__name__)


class RunCommandTool(BaseTool):
    """Tool for executing shell commands with strict security restrictions.

    Security Features:
        - REQUIRES explicit command allowlist (no fallback to blocklist)
        - shell=True is REMOVED entirely (prevents command injection)
        - Commands are parsed with shlex for safe argument handling
        - Timeout enforcement prevents runaway processes (max 5 min)
        - All executions are logged for audit

    Example:
        >>> tool = RunCommandTool(allowed_commands=["git", "ls", "cat"])
        >>> result = await tool.execute(command="git status")

    Note:
        The shell=True option has been REMOVED because it allows:
        - Command chaining (;, &&, ||)
        - Command substitution ($(), ``)
        - Pipe injection (|)
        - Blocklist bypass (/bin/rm, busybox rm)
    """

    def __init__(
        self,
        allowed_commands: list[str],
        timeout: float = 30.0,
        working_dir: str | None = None,
    ):
        """Initialize run_command tool.

        Args:
            allowed_commands: Whitelist of allowed commands (REQUIRED)
            timeout: Command timeout in seconds (default: 30, max: 300)
            working_dir: Working directory for command execution

        Raises:
            ValueError: If allowed_commands is empty or None
        """
        if not allowed_commands:
            raise ValueError(
                "allowed_commands is required for security. "
                "Shell command execution without an allowlist is not permitted."
            )

        super().__init__(
            name="run_command",
            description="Execute a command from the allowed list",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute (base command must be in allowed list)",
                    },
                },
                "required": ["command"],
            },
            permissions=["shell:execute"],
        )
        self.allowed_commands = set(allowed_commands)
        self.timeout = min(timeout, 300.0)  # Cap at 5 minutes for safety
        self.working_dir = working_dir

    async def _execute(
        self,
        command: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute command safely without shell interpretation.

        Args:
            command: Command string to execute

        Returns:
            Dictionary with command output and metadata

        Raises:
            PermissionError: If command is not in allowed list
            ToolError: If command execution fails or times out
        """
        # Parse command with shlex for safe argument handling
        try:
            parsed = shlex.split(command)
            if not parsed:
                raise ToolError(
                    self.name,
                    "Empty command",
                    {"command": command},
                )
            base_cmd = parsed[0]
        except ValueError as e:
            raise ToolError(
                self.name,
                f"Invalid command syntax: {e}",
                {"command": command},
            )

        # Security check: command must be in allowlist
        if base_cmd not in self.allowed_commands:
            logger.warning(
                f"Blocked command execution: {base_cmd}",
                extra={"command": command, "base_cmd": base_cmd},
            )
            raise PermissionError(
                self.name,
                f"Command '{base_cmd}' is not in allowed commands",
                {
                    "command": command,
                    "base_command": base_cmd,
                    "allowed_commands": list(self.allowed_commands),
                },
            )

        # Log the execution for audit
        logger.info(
            f"Executing command: {base_cmd}",
            extra={"command": command, "working_dir": self.working_dir},
        )

        # Execute command WITHOUT shell (safe mode only)
        try:
            process = await asyncio.create_subprocess_exec(
                *parsed,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()  # Ensure process is cleaned up
                logger.warning(
                    f"Command timed out: {base_cmd}",
                    extra={"command": command, "timeout": self.timeout},
                )
                raise ToolError(
                    self.name,
                    f"Command timed out after {self.timeout}s",
                    {"command": command},
                )

            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "return_code": process.returncode,
                "success": process.returncode == 0,
                "command": command,
            }

        except FileNotFoundError:
            raise ToolError(
                self.name,
                f"Command not found: {base_cmd}",
                {"command": command, "base_command": base_cmd},
            )
        except PermissionError as e:
            raise ToolError(
                self.name,
                f"Permission denied executing {base_cmd}: {e}",
                {"command": command},
            )
        except Exception as e:
            raise ToolError(
                self.name,
                f"Command execution failed: {e}",
                {"command": command},
            )


# =============================================================================
# Factory Function for Secure Command Tool Creation
# =============================================================================


def create_command_tool(
    allowed_commands: list[str],
    timeout: float = 30.0,
    working_dir: str | None = None,
) -> RunCommandTool:
    """Create a command execution tool with explicit allowlist.

    This is the recommended way to create command execution tools.

    Args:
        allowed_commands: List of commands that can be executed
        timeout: Maximum execution time in seconds (default: 30, max: 300)
        working_dir: Working directory for commands

    Returns:
        Configured RunCommandTool instance

    Example:
        >>> tool = create_command_tool(
        ...     allowed_commands=["git", "ls", "cat"],
        ...     timeout=60.0
        ... )
        >>> result = await tool.execute(command="git status")
    """
    return RunCommandTool(
        allowed_commands=allowed_commands,
        timeout=timeout,
        working_dir=working_dir,
    )


# =============================================================================
# Predefined Safe Command Sets
# =============================================================================


# Read-only commands that don't modify system state
READONLY_COMMANDS = [
    "cat",
    "head",
    "tail",
    "less",
    "more",  # File viewing
    "ls",
    "dir",
    "tree",  # Directory listing
    "grep",
    "find",
    "which",
    "whereis",  # Search
    "pwd",
    "whoami",
    "hostname",
    "uname",
    "date",  # System info
    "file",
    "stat",
    "wc",  # File info
]

# Development commands (includes some that can modify files)
DEVELOPMENT_COMMANDS = READONLY_COMMANDS + [
    "git",  # Version control
    "python",
    "python3",  # Python interpreter
    "pip",
    "pip3",
    "uv",
    "poetry",  # Package managers
    "npm",
    "node",  # Node.js
    "pytest",
    "make",  # Testing/building
]


def create_readonly_command_tool(
    working_dir: str | None = None,
    timeout: float = 30.0,
) -> RunCommandTool:
    """Create a command tool limited to read-only operations.

    Args:
        working_dir: Working directory for commands
        timeout: Maximum execution time

    Returns:
        RunCommandTool with read-only commands only
    """
    return RunCommandTool(
        allowed_commands=READONLY_COMMANDS,
        timeout=timeout,
        working_dir=working_dir,
    )


def create_development_command_tool(
    working_dir: str | None = None,
    timeout: float = 60.0,
) -> RunCommandTool:
    """Create a command tool for development operations.

    Includes git, python, package managers, and testing tools.

    Args:
        working_dir: Working directory for commands
        timeout: Maximum execution time

    Returns:
        RunCommandTool with development commands
    """
    return RunCommandTool(
        allowed_commands=DEVELOPMENT_COMMANDS,
        timeout=timeout,
        working_dir=working_dir,
    )


# =============================================================================
# DEPRECATED: Default instance removed for security
# =============================================================================
# The default 'run_command' instance has been REMOVED because:
# 1. It allowed broad command execution without explicit configuration
# 2. The shell=True option (now removed) was a security risk
#
# Migration:
#   # Old (less secure):
#   from paracle_tools.builtin.shell import run_command
#   result = await run_command.execute(command="git status")
#
#   # New (secure):
#   from paracle_tools.builtin.shell import create_development_command_tool
#   tool = create_development_command_tool(working_dir="/app")
#   result = await tool.execute(command="git status")
# =============================================================================
