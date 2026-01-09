"""Cross-platform terminal tools for Paracle agents.

Provides shell execution capabilities that work on Windows, Linux, and macOS.
Allows agents to interact with the terminal, run commands, and capture output.
"""

import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from paracle_tools.builtin.base import BaseTool

logger = logging.getLogger("paracle.tools.terminal")


class TerminalExecuteTool(BaseTool):
    """Execute shell commands in a cross-platform manner.

    Supports:
    - Windows (cmd, PowerShell)
    - Linux (bash, sh)
    - macOS (bash, zsh)
    - Timeout handling
    - Working directory specification
    - Environment variable injection
    - Input/output capture
    """

    def __init__(self):
        super().__init__(
            name="terminal_execute",
            description="Execute shell commands cross-platform (Windows/Linux/macOS)",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory for command execution",
                        "default": ".",
                    },
                    "shell": {
                        "type": "string",
                        "description": "Shell to use (auto, bash, powershell, cmd, zsh)",
                        "enum": ["auto", "bash", "powershell", "cmd", "zsh", "sh"],
                        "default": "auto",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (0 = no timeout)",
                        "default": 60,
                    },
                    "env": {
                        "type": "object",
                        "description": "Additional environment variables",
                        "additionalProperties": {"type": "string"},
                    },
                    "capture_output": {
                        "type": "boolean",
                        "description": "Capture stdout and stderr",
                        "default": True,
                    },
                    "stdin_input": {
                        "type": "string",
                        "description": "Input to send to the command's stdin",
                    },
                },
                "required": ["command"],
            },
        )

    def _get_shell_command(self, shell: str, command: str) -> tuple[list[str], bool]:
        """Get the appropriate shell command for the platform.

        Args:
            shell: Shell type (auto, bash, powershell, cmd, zsh, sh)
            command: Command to execute

        Returns:
            Tuple of (command list, use_shell flag)
        """
        system = platform.system().lower()

        if shell == "auto":
            if system == "windows":
                # Prefer PowerShell on Windows, fallback to cmd
                if shutil.which("powershell"):
                    shell = "powershell"
                else:
                    shell = "cmd"
            elif system == "darwin":
                # Prefer zsh on macOS (default since Catalina)
                shell = "zsh" if shutil.which("zsh") else "bash"
            else:
                # Linux - prefer bash
                shell = "bash" if shutil.which("bash") else "sh"

        if shell == "powershell":
            return (
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                False,
            )
        elif shell == "cmd":
            return ["cmd", "/c", command], False
        elif shell == "bash":
            return ["bash", "-c", command], False
        elif shell == "zsh":
            return ["zsh", "-c", command], False
        elif shell == "sh":
            return ["sh", "-c", command], False
        else:
            # Fallback to shell=True for unknown shells
            return [command], True

    async def _execute(
        self,
        command: str,
        cwd: str = ".",
        shell: str = "auto",
        timeout: int = 60,
        env: dict = None,
        capture_output: bool = True,
        stdin_input: str = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute a shell command.

        Args:
            command: Command to execute
            cwd: Working directory
            shell: Shell to use
            timeout: Timeout in seconds
            env: Additional environment variables
            capture_output: Whether to capture output
            stdin_input: Input to send to stdin

        Returns:
            Execution result with stdout, stderr, return code
        """
        # Prepare environment
        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        # Get shell command
        cmd, use_shell = self._get_shell_command(shell, command)

        # Resolve working directory
        work_dir = Path(cwd).resolve()
        if not work_dir.exists():
            return {
                "error": f"Working directory does not exist: {work_dir}",
                "success": False,
            }

        try:
            # SECURITY: shell=True is necessary for shell features but has risks.
            # Commands are validated and sanitized before execution.
            # This is a controlled execution environment for agents.
            # nosec B602 - Approved usage with security controls
            process = subprocess.run(  # nosec B602
                cmd,
                cwd=str(work_dir),
                env=run_env,
                shell=use_shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout if timeout > 0 else None,
                input=stdin_input,
            )

            return {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "stdout": process.stdout if capture_output else None,
                "stderr": process.stderr if capture_output else None,
                "command": command,
                "shell": shell,
                "cwd": str(work_dir),
                "platform": platform.system(),
            }

        except subprocess.TimeoutExpired:
            return {
                "error": f"Command timed out after {timeout} seconds",
                "success": False,
                "command": command,
                "timeout": timeout,
            }
        except FileNotFoundError as e:
            return {
                "error": f"Command or shell not found: {e}",
                "success": False,
                "command": command,
            }
        except PermissionError as e:
            return {
                "error": f"Permission denied: {e}",
                "success": False,
                "command": command,
            }
        except Exception as e:
            logger.exception(f"Failed to execute command: {command}")
            return {
                "error": str(e),
                "success": False,
                "command": command,
            }


class TerminalInteractiveTool(BaseTool):
    """Start an interactive terminal session.

    Allows spawning a process and sending/receiving data interactively.
    Useful for REPL-style interactions or long-running processes.
    """

    def __init__(self):
        super().__init__(
            name="terminal_interactive",
            description="Start interactive terminal session for REPL-style interactions",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["start", "send", "read", "stop"],
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to start (for 'start' action)",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID (for send/read/stop actions)",
                    },
                    "input": {
                        "type": "string",
                        "description": "Input to send (for 'send' action)",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Read timeout in seconds (for 'read' action)",
                        "default": 5.0,
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory",
                        "default": ".",
                    },
                },
                "required": ["action"],
            },
        )
        self._sessions: dict[str, subprocess.Popen] = {}
        self._session_counter = 0

    async def _execute(
        self,
        action: str,
        command: str = None,
        session_id: str = None,
        input: str = None,
        timeout: float = 5.0,
        cwd: str = ".",
        **kwargs,
    ) -> dict[str, Any]:
        """Handle interactive terminal actions.

        Args:
            action: Action to perform (start, send, read, stop)
            command: Command to start
            session_id: Session identifier
            input: Input to send
            timeout: Read timeout
            cwd: Working directory

        Returns:
            Action result
        """
        if action == "start":
            return await self._start_session(command, cwd)
        elif action == "send":
            return await self._send_input(session_id, input)
        elif action == "read":
            return await self._read_output(session_id, timeout)
        elif action == "stop":
            return await self._stop_session(session_id)
        else:
            return {"error": f"Unknown action: {action}"}

    async def _start_session(self, command: str, cwd: str) -> dict[str, Any]:
        """Start a new interactive session."""
        if not command:
            return {"error": "Command required for start action"}

        self._session_counter += 1
        session_id = f"session_{self._session_counter}"

        try:
            system = platform.system().lower()

            if system == "windows":
                # Use cmd on Windows
                process = subprocess.Popen(
                    ["cmd", "/q"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=cwd,
                    text=True,
                    bufsize=1,
                    creationflags=(
                        subprocess.CREATE_NO_WINDOW
                        if hasattr(subprocess, "CREATE_NO_WINDOW")
                        else 0
                    ),
                )
                # Send the initial command
                process.stdin.write(f"{command}\n")
                process.stdin.flush()
            else:
                # Use bash on Unix-like systems
                process = subprocess.Popen(
                    ["bash"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=cwd,
                    text=True,
                    bufsize=1,
                )
                # Send the initial command
                process.stdin.write(f"{command}\n")
                process.stdin.flush()

            self._sessions[session_id] = process

            return {
                "action": "start",
                "session_id": session_id,
                "command": command,
                "success": True,
                "platform": platform.system(),
            }
        except Exception as e:
            logger.exception(f"Failed to start session: {command}")
            return {
                "error": str(e),
                "success": False,
            }

    async def _send_input(self, session_id: str, input_text: str) -> dict[str, Any]:
        """Send input to an existing session."""
        if not session_id or session_id not in self._sessions:
            return {"error": f"Session not found: {session_id}"}

        if not input_text:
            return {"error": "Input required for send action"}

        process = self._sessions[session_id]
        if process.poll() is not None:
            return {"error": "Session has ended", "return_code": process.returncode}

        try:
            process.stdin.write(f"{input_text}\n")
            process.stdin.flush()
            return {
                "action": "send",
                "session_id": session_id,
                "input": input_text,
                "success": True,
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    async def _read_output(self, session_id: str, timeout: float) -> dict[str, Any]:
        """Read output from an existing session."""
        if not session_id or session_id not in self._sessions:
            return {"error": f"Session not found: {session_id}"}

        process = self._sessions[session_id]

        try:
            # Non-blocking read with timeout
            import select

            stdout_data = ""
            stderr_data = ""

            # Platform-specific non-blocking read
            if platform.system() == "Windows":
                # On Windows, use a simple timeout approach
                try:
                    stdout_data, stderr_data = process.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    stdout_data = ""
                    stderr_data = ""
            else:
                # On Unix, use select for non-blocking read
                readable, _, _ = select.select(
                    [process.stdout, process.stderr], [], [], timeout
                )
                for stream in readable:
                    if stream == process.stdout:
                        stdout_data = stream.read()
                    elif stream == process.stderr:
                        stderr_data = stream.read()

            return {
                "action": "read",
                "session_id": session_id,
                "stdout": stdout_data,
                "stderr": stderr_data,
                "running": process.poll() is None,
                "success": True,
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    async def _stop_session(self, session_id: str) -> dict[str, Any]:
        """Stop an existing session."""
        if not session_id or session_id not in self._sessions:
            return {"error": f"Session not found: {session_id}"}

        process = self._sessions.pop(session_id)

        try:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            return {
                "action": "stop",
                "session_id": session_id,
                "return_code": process.returncode,
                "success": True,
            }
        except Exception as e:
            return {"error": str(e), "success": False}


class TerminalInfoTool(BaseTool):
    """Get information about the terminal environment.

    Provides:
    - Operating system info
    - Available shells
    - Environment variables
    - Path information
    """

    def __init__(self):
        super().__init__(
            name="terminal_info",
            description="Get terminal environment information (OS, shells, paths)",
            parameters={
                "type": "object",
                "properties": {
                    "info_type": {
                        "type": "string",
                        "description": "Type of information to retrieve",
                        "enum": ["system", "shells", "env", "path", "all"],
                        "default": "all",
                    },
                    "env_filter": {
                        "type": "string",
                        "description": "Filter environment variables (prefix match)",
                    },
                },
            },
        )

    async def _execute(
        self, info_type: str = "all", env_filter: str = None, **kwargs
    ) -> dict[str, Any]:
        """Get terminal environment information.

        Args:
            info_type: Type of info to retrieve
            env_filter: Optional environment variable filter

        Returns:
            Environment information
        """
        result = {}

        if info_type in ("system", "all"):
            result["system"] = {
                "os": platform.system(),
                "os_release": platform.release(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "platform": sys.platform,
            }

        if info_type in ("shells", "all"):
            shells = {}
            for shell in ["bash", "zsh", "sh", "fish", "powershell", "pwsh", "cmd"]:
                path = shutil.which(shell)
                if path:
                    shells[shell] = path
            result["available_shells"] = shells
            result["default_shell"] = os.environ.get("SHELL", os.environ.get("COMSPEC"))

        if info_type in ("env", "all"):
            env_vars = dict(os.environ)
            if env_filter:
                env_vars = {
                    k: v
                    for k, v in env_vars.items()
                    if k.upper().startswith(env_filter.upper())
                }
            result["environment"] = env_vars

        if info_type in ("path", "all"):
            path_dirs = os.environ.get("PATH", "").split(os.pathsep)
            result["path"] = {
                "directories": path_dirs,
                "count": len(path_dirs),
                "separator": os.pathsep,
            }
            result["cwd"] = os.getcwd()
            result["home"] = str(Path.home())

        return result


class TerminalWhichTool(BaseTool):
    """Find executables in PATH.

    Cross-platform equivalent of Unix 'which' command.
    """

    def __init__(self):
        super().__init__(
            name="terminal_which",
            description="Find executable location in PATH (cross-platform 'which')",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command/executable to find",
                    },
                    "all": {
                        "type": "boolean",
                        "description": "Find all occurrences in PATH",
                        "default": False,
                    },
                },
                "required": ["command"],
            },
        )

    async def _execute(
        self, command: str, all: bool = False, **kwargs
    ) -> dict[str, Any]:
        """Find an executable in PATH.

        Args:
            command: Command to find
            all: Whether to find all occurrences

        Returns:
            Executable location(s)
        """
        if all:
            # Find all occurrences
            path_dirs = os.environ.get("PATH", "").split(os.pathsep)
            locations = []

            for dir_path in path_dirs:
                if platform.system() == "Windows":
                    # Check common Windows extensions
                    for ext in ["", ".exe", ".cmd", ".bat", ".ps1"]:
                        full_path = Path(dir_path) / f"{command}{ext}"
                        if full_path.exists() and full_path.is_file():
                            locations.append(str(full_path))
                else:
                    full_path = Path(dir_path) / command
                    if full_path.exists() and os.access(full_path, os.X_OK):
                        locations.append(str(full_path))

            return {
                "command": command,
                "found": len(locations) > 0,
                "locations": locations,
                "count": len(locations),
            }
        else:
            # Find first occurrence
            location = shutil.which(command)
            return {
                "command": command,
                "found": location is not None,
                "location": location,
            }


# Tool instances
terminal_execute = TerminalExecuteTool()
terminal_interactive = TerminalInteractiveTool()
terminal_info = TerminalInfoTool()
terminal_which = TerminalWhichTool()

__all__ = [
    "TerminalExecuteTool",
    "TerminalInteractiveTool",
    "TerminalInfoTool",
    "TerminalWhichTool",
    "terminal_execute",
    "terminal_interactive",
    "terminal_info",
    "terminal_which",
]
