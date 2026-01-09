"""Shell Capability for MetaAgent.

Provides shell and command execution:
- Execute shell commands
- Run scripts
- Process management
- Environment management
- Safe command execution with sandboxing

Example:
    >>> cap = ShellCapability()
    >>> await cap.initialize()
    >>>
    >>> # Run command
    >>> result = await cap.run("ls -la")
    >>>
    >>> # Run Python script
    >>> result = await cap.run_python_script("script.py", args=["--help"])
    >>>
    >>> # Background process
    >>> result = await cap.run_background("npm run dev")
"""

import asyncio
import os
import platform
import shlex
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class ShellConfig(CapabilityConfig):
    """Configuration for Shell capability."""

    working_directory: str | None = Field(
        default=None, description="Working directory for commands (defaults to cwd)"
    )
    shell: str | None = Field(
        default=None, description="Shell to use (defaults to system shell)"
    )
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Additional environment variables"
    )
    inherit_env: bool = Field(default=True, description="Inherit current environment")
    max_output_size: int = Field(
        default=1024 * 1024, ge=1024, description="Maximum output size in bytes"  # 1 MB
    )
    allowed_commands: list[str] | None = Field(
        default=None, description="Allowed command prefixes (None = all)"
    )
    blocked_commands: list[str] = Field(
        default_factory=lambda: ["rm -rf /", "mkfs", "dd if=", ":(){:|:&};:"],
        description="Blocked command patterns",
    )
    enable_background: bool = Field(
        default=True, description="Enable background process execution"
    )
    default_timeout: float = Field(
        default=60.0,
        ge=1.0,
        le=3600.0,
        description="Default command timeout in seconds",
    )


class ProcessInfo:
    """Information about a running process."""

    def __init__(
        self,
        pid: int,
        command: str,
        started_at: datetime,
    ):
        self.pid = pid
        self.command = command
        self.started_at = started_at
        self.process: asyncio.subprocess.Process | None = None
        self.output_buffer: list[str] = []
        self.error_buffer: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pid": self.pid,
            "command": self.command,
            "started_at": self.started_at.isoformat(),
            "running": self.process is not None and self.process.returncode is None,
        }


class ShellCapability(BaseCapability):
    """Shell command execution capability.

    Provides safe command execution with:
    - Command validation and sandboxing
    - Output capture and streaming
    - Background process management
    - Environment management
    - Cross-platform support

    Example:
        >>> cap = ShellCapability()
        >>> await cap.initialize()
        >>>
        >>> # Simple command
        >>> result = await cap.run("echo 'Hello'")
        >>> print(result.output["stdout"])
        >>>
        >>> # With timeout
        >>> result = await cap.run("long_command", timeout=30)
    """

    name = "shell"
    description = "Shell command execution with safety features"

    def __init__(self, config: ShellConfig | None = None):
        """Initialize Shell capability."""
        super().__init__(config or ShellConfig())
        self.config: ShellConfig = self.config

        self._working_dir: Path | None = None
        self._env: dict[str, str] = {}
        self._background_processes: dict[int, ProcessInfo] = {}

    async def initialize(self) -> None:
        """Initialize capability."""
        await super().initialize()

        # Set working directory
        if self.config.working_directory:
            self._working_dir = Path(self.config.working_directory).resolve()
        else:
            self._working_dir = Path.cwd()

        # Set up environment
        if self.config.inherit_env:
            self._env = dict(os.environ)
        self._env.update(self.config.env_vars)

    async def shutdown(self) -> None:
        """Shutdown and cleanup processes."""
        # Terminate background processes
        for pid, info in list(self._background_processes.items()):
            if info.process and info.process.returncode is None:
                try:
                    info.process.terminate()
                    await asyncio.wait_for(info.process.wait(), timeout=5.0)
                except (asyncio.TimeoutError, ProcessLookupError):
                    info.process.kill()

        self._background_processes.clear()
        await super().shutdown()

    def _validate_command(self, command: str) -> None:
        """Validate command against security rules.

        Raises:
            ValueError: If command is blocked or not allowed
        """
        # Check blocked patterns
        for blocked in self.config.blocked_commands:
            if blocked.lower() in command.lower():
                raise ValueError(f"Command blocked by security policy: {blocked}")

        # Check allowed commands
        if self.config.allowed_commands:
            allowed = False
            for prefix in self.config.allowed_commands:
                if command.startswith(prefix):
                    allowed = True
                    break
            if not allowed:
                raise ValueError(
                    f"Command not in allowed list. Allowed: {self.config.allowed_commands}"
                )

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute shell operation.

        Actions:
            - run: Execute command and wait
            - run_background: Execute in background
            - run_script: Execute a script file
            - kill: Kill a background process
            - list_processes: List background processes
            - get_output: Get output from background process
            - which: Find command path
            - env: Get/set environment variables
            - cwd: Get/change working directory
        """
        action = kwargs.get("action", "run")
        start_time = time.time()

        try:
            if action == "run":
                result = await self._run(
                    command=kwargs.get("command", ""),
                    timeout=kwargs.get("timeout", self.config.default_timeout),
                    shell=kwargs.get("shell", True),
                    capture_output=kwargs.get("capture_output", True),
                )
            elif action == "run_background":
                result = await self._run_background(
                    command=kwargs.get("command", ""),
                )
            elif action == "run_script":
                result = await self._run_script(
                    script_path=kwargs.get("script_path", ""),
                    args=kwargs.get("args", []),
                    interpreter=kwargs.get("interpreter"),
                    timeout=kwargs.get("timeout", self.config.default_timeout),
                )
            elif action == "kill":
                result = await self._kill_process(
                    pid=kwargs.get("pid", 0),
                    force=kwargs.get("force", False),
                )
            elif action == "list_processes":
                result = await self._list_processes()
            elif action == "get_output":
                result = await self._get_output(
                    pid=kwargs.get("pid", 0),
                )
            elif action == "which":
                result = await self._which(kwargs.get("command", ""))
            elif action == "env":
                if "set" in kwargs:
                    result = await self._set_env(
                        kwargs.get("name", ""),
                        kwargs.get("value", ""),
                    )
                elif "unset" in kwargs:
                    result = await self._unset_env(kwargs.get("name", ""))
                else:
                    result = await self._get_env(kwargs.get("name"))
            elif action == "cwd":
                if "path" in kwargs:
                    result = await self._change_dir(kwargs.get("path", ""))
                else:
                    result = await self._get_cwd()
            elif action == "system_info":
                result = await self._system_info()
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    async def _run(
        self,
        command: str,
        timeout: float = 60.0,
        shell: bool = True,
        capture_output: bool = True,
    ) -> dict[str, Any]:
        """Execute command and wait for completion."""
        if not command:
            raise ValueError("Command is required")

        self._validate_command(command)

        start_time = time.time()

        try:
            if shell:
                # Use shell
                if platform.system() == "Windows":
                    proc = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE if capture_output else None,
                        stderr=asyncio.subprocess.PIPE if capture_output else None,
                        cwd=str(self._working_dir),
                        env=self._env,
                    )
                else:
                    proc = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE if capture_output else None,
                        stderr=asyncio.subprocess.PIPE if capture_output else None,
                        cwd=str(self._working_dir),
                        env=self._env,
                    )
            else:
                # Direct execution
                args = shlex.split(command)
                proc = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE if capture_output else None,
                    stderr=asyncio.subprocess.PIPE if capture_output else None,
                    cwd=str(self._working_dir),
                    env=self._env,
                )

            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )

            duration = time.time() - start_time

            return {
                "command": command,
                "return_code": proc.returncode,
                "stdout": self._decode_output(stdout, capture_output),
                "stderr": self._decode_output(stderr, capture_output),
                "success": proc.returncode == 0,
                "duration_seconds": duration,
                "pid": proc.pid,
            }

        except asyncio.TimeoutError:
            proc.kill()
            return {
                "command": command,
                "return_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "success": False,
                "timeout": True,
                "duration_seconds": timeout,
            }

    def _decode_output(
        self,
        output: bytes | None,
        captured: bool,
    ) -> str:
        """Decode command output."""
        if not captured or output is None:
            return ""

        # Truncate if too large
        if len(output) > self.config.max_output_size:
            output = output[: self.config.max_output_size]
            truncated = True
        else:
            truncated = False

        try:
            decoded = output.decode("utf-8")
        except UnicodeDecodeError:
            decoded = output.decode("utf-8", errors="replace")

        if truncated:
            decoded += "\n... (output truncated)"

        return decoded

    async def _run_background(self, command: str) -> dict[str, Any]:
        """Execute command in background."""
        if not self.config.enable_background:
            raise ValueError("Background execution is disabled")

        if not command:
            raise ValueError("Command is required")

        self._validate_command(command)

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self._working_dir),
            env=self._env,
        )

        info = ProcessInfo(
            pid=proc.pid,
            command=command,
            started_at=datetime.now(timezone.utc),
        )
        info.process = proc
        self._background_processes[proc.pid] = info

        # Start output collection task
        asyncio.create_task(self._collect_output(info))

        return {
            "pid": proc.pid,
            "command": command,
            "started": True,
            "background": True,
        }

    async def _collect_output(self, info: ProcessInfo) -> None:
        """Collect output from background process."""
        if not info.process:
            return

        async def read_stream(stream, buffer):
            while True:
                line = await stream.readline()
                if not line:
                    break
                buffer.append(line.decode("utf-8", errors="replace"))

        await asyncio.gather(
            read_stream(info.process.stdout, info.output_buffer),
            read_stream(info.process.stderr, info.error_buffer),
        )

    async def _run_script(
        self,
        script_path: str,
        args: list[str] = None,
        interpreter: str | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """Execute a script file."""
        path = Path(script_path)
        if not path.is_absolute():
            path = self._working_dir / path

        if not path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        # Determine interpreter
        if not interpreter:
            ext = path.suffix.lower()
            interpreters = {
                ".py": sys.executable,
                ".sh": "/bin/bash" if platform.system() != "Windows" else "bash",
                ".js": "node",
                ".ts": "ts-node",
                ".rb": "ruby",
            }
            interpreter = interpreters.get(ext, "")

        if interpreter:
            command = f'{interpreter} "{path}"'
        else:
            command = str(path)

        if args:
            command += " " + " ".join(shlex.quote(arg) for arg in args)

        return await self._run(command, timeout=timeout)

    async def _kill_process(
        self,
        pid: int,
        force: bool = False,
    ) -> dict[str, Any]:
        """Kill a background process."""
        info = self._background_processes.get(pid)
        if not info:
            raise ValueError(f"Process not found: {pid}")

        if info.process and info.process.returncode is None:
            if force:
                info.process.kill()
            else:
                info.process.terminate()

            try:
                await asyncio.wait_for(info.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                info.process.kill()

        del self._background_processes[pid]

        return {
            "pid": pid,
            "killed": True,
            "force": force,
        }

    async def _list_processes(self) -> dict[str, Any]:
        """List background processes."""
        processes = []
        for pid, info in self._background_processes.items():
            proc_info = info.to_dict()
            if info.process:
                proc_info["return_code"] = info.process.returncode
            processes.append(proc_info)

        return {
            "processes": processes,
            "count": len(processes),
        }

    async def _get_output(self, pid: int) -> dict[str, Any]:
        """Get output from background process."""
        info = self._background_processes.get(pid)
        if not info:
            raise ValueError(f"Process not found: {pid}")

        return {
            "pid": pid,
            "stdout": "".join(info.output_buffer),
            "stderr": "".join(info.error_buffer),
            "running": info.process is not None and info.process.returncode is None,
            "return_code": info.process.returncode if info.process else None,
        }

    async def _which(self, command: str) -> dict[str, Any]:
        """Find command path."""
        import shutil

        path = shutil.which(command)
        return {
            "command": command,
            "path": path,
            "found": path is not None,
        }

    async def _get_env(self, name: str | None = None) -> dict[str, Any]:
        """Get environment variables."""
        if name:
            return {
                "name": name,
                "value": self._env.get(name),
                "exists": name in self._env,
            }
        return {"env": dict(self._env)}

    async def _set_env(self, name: str, value: str) -> dict[str, Any]:
        """Set environment variable."""
        self._env[name] = value
        return {"name": name, "value": value, "set": True}

    async def _unset_env(self, name: str) -> dict[str, Any]:
        """Unset environment variable."""
        existed = name in self._env
        if existed:
            del self._env[name]
        return {"name": name, "unset": existed}

    async def _get_cwd(self) -> dict[str, Any]:
        """Get current working directory."""
        return {"cwd": str(self._working_dir)}

    async def _change_dir(self, path: str) -> dict[str, Any]:
        """Change working directory."""
        new_path = Path(path)
        if not new_path.is_absolute():
            new_path = self._working_dir / new_path

        new_path = new_path.resolve()
        if not new_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not new_path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        self._working_dir = new_path
        return {"cwd": str(self._working_dir)}

    async def _system_info(self) -> dict[str, Any]:
        """Get system information."""
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "cwd": str(self._working_dir),
        }

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def run(
        self,
        command: str,
        timeout: float = 60.0,
        **kwargs,
    ) -> CapabilityResult:
        """Run a command."""
        return await self.execute(
            action="run",
            command=command,
            timeout=timeout,
            **kwargs,
        )

    async def run_background(self, command: str) -> CapabilityResult:
        """Run command in background."""
        return await self.execute(action="run_background", command=command)

    async def run_python_script(
        self,
        script_path: str,
        args: list[str] = None,
        timeout: float = 60.0,
    ) -> CapabilityResult:
        """Run a Python script."""
        return await self.execute(
            action="run_script",
            script_path=script_path,
            args=args,
            interpreter=sys.executable,
            timeout=timeout,
        )

    async def which(self, command: str) -> CapabilityResult:
        """Find command path."""
        return await self.execute(action="which", command=command)

    async def system_info(self) -> CapabilityResult:
        """Get system information."""
        return await self.execute(action="system_info")
