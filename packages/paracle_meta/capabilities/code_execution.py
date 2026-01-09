"""Code execution capability for MetaAgent.

Provides secure code execution, testing, and analysis
capabilities for the MetaAgent.
"""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class CodeExecutionConfig(CapabilityConfig):
    """Configuration for code execution capability."""

    # Security settings
    allowed_languages: list[str] = Field(
        default=["python"],
        description="Allowed programming languages",
    )
    max_execution_time: float = Field(
        default=60.0, ge=1.0, le=300.0, description="Max execution time in seconds"
    )
    max_memory_mb: int = Field(
        default=512, ge=64, le=4096, description="Max memory usage in MB"
    )
    allow_network: bool = Field(
        default=False, description="Allow network access during execution"
    )
    allow_file_write: bool = Field(
        default=True, description="Allow writing files in temp directory"
    )

    # Working directory
    working_dir: str | None = Field(
        default=None, description="Working directory for execution"
    )

    # Python settings
    python_path: str | None = Field(
        default=None, description="Path to Python interpreter"
    )
    install_packages: bool = Field(
        default=True, description="Allow installing packages"
    )


class ExecutionResult:
    """Result of code execution."""

    def __init__(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        duration_ms: float,
        language: str,
        files_created: list[str] | None = None,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.duration_ms = duration_ms
        self.language = language
        self.files_created = files_created or []
        self.success = return_code == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "duration_ms": self.duration_ms,
            "language": self.language,
            "files_created": self.files_created,
            "success": self.success,
        }


class CodeExecutionCapability(BaseCapability):
    """Code execution capability for MetaAgent.

    Provides secure execution of code in various languages,
    with resource limits and isolation.

    Example:
        >>> code_exec = CodeExecutionCapability()
        >>> await code_exec.initialize()
        >>>
        >>> # Execute Python code
        >>> result = await code_exec.execute(
        ...     code="print('Hello, World!')",
        ...     language="python"
        ... )
        >>>
        >>> # Run tests
        >>> result = await code_exec.execute(
        ...     action="test",
        ...     test_path="tests/",
        ...     coverage=True
        ... )
        >>>
        >>> # Analyze code
        >>> result = await code_exec.execute(
        ...     action="analyze",
        ...     code="def foo(): pass",
        ...     checks=["lint", "type"]
        ... )
    """

    name = "code_execution"
    description = "Execute code, run tests, and analyze code quality"

    def __init__(self, config: CodeExecutionConfig | None = None):
        """Initialize code execution capability.

        Args:
            config: Execution configuration
        """
        super().__init__(config or CodeExecutionConfig())
        self.config: CodeExecutionConfig = self.config
        self._temp_dir: Path | None = None

    async def initialize(self) -> None:
        """Initialize execution environment."""
        # Create temp directory for execution
        self._temp_dir = Path(tempfile.mkdtemp(prefix="paracle_meta_"))
        await super().initialize()

    async def shutdown(self) -> None:
        """Cleanup execution environment."""
        # Clean up temp directory
        if self._temp_dir and self._temp_dir.exists():
            import shutil

            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute code capability.

        Args:
            action: Action to perform (run, test, analyze, install)
            **kwargs: Action-specific parameters

        Returns:
            CapabilityResult with execution outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "run")
        start_time = time.time()

        try:
            if action == "run":
                result = await self._run_code(**kwargs)
            elif action == "test":
                result = await self._run_tests(**kwargs)
            elif action == "analyze":
                result = await self._analyze_code(**kwargs)
            elif action == "install":
                result = await self._install_packages(**kwargs)
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

    async def _run_code(
        self,
        code: str,
        language: str = "python",
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Run code in specified language.

        Args:
            code: Code to execute
            language: Programming language
            filename: Optional filename for the script
            args: Command line arguments
            env: Environment variables

        Returns:
            Execution result
        """
        # Validate language
        if language not in self.config.allowed_languages:
            raise ValueError(
                f"Language '{language}' not allowed. "
                f"Allowed: {self.config.allowed_languages}"
            )

        if language == "python":
            return await self._run_python(code, filename, args, env)
        else:
            raise ValueError(f"Language '{language}' not yet implemented")

    async def _run_python(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Run Python code.

        Args:
            code: Python code to execute
            filename: Optional script filename
            args: Command line arguments
            env: Environment variables

        Returns:
            Execution result dictionary
        """
        # Write code to temp file
        if not self._temp_dir:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="paracle_meta_"))

        script_name = filename or "script.py"
        script_path = self._temp_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        # Build command
        python_path = self.config.python_path or sys.executable
        cmd = [python_path, str(script_path)]
        if args:
            cmd.extend(args)

        # Build environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        # Restrict network if configured
        if not self.config.allow_network:
            exec_env["PARACLE_NO_NETWORK"] = "1"

        # Execute
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._temp_dir),
                env=exec_env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.max_execution_time,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(
                    f"Execution timed out after {self.config.max_execution_time}s"
                )

            duration_ms = (time.time() - start_time) * 1000

            # List created files
            files_created = []
            if self.config.allow_file_write:
                for f in self._temp_dir.iterdir():
                    if f.name != script_name:
                        files_created.append(f.name)

            return ExecutionResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                return_code=process.returncode or 0,
                duration_ms=duration_ms,
                language="python",
                files_created=files_created,
            ).to_dict()

        finally:
            # Clean up script file
            if script_path.exists():
                script_path.unlink()

    async def _run_tests(
        self,
        test_path: str = "tests/",
        coverage: bool = False,
        verbose: bool = True,
        pattern: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Run tests with pytest.

        Args:
            test_path: Path to tests
            coverage: Enable coverage reporting
            verbose: Verbose output
            pattern: Test file pattern

        Returns:
            Test results
        """
        working_dir = self.config.working_dir or os.getcwd()

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(["--cov=.", "--cov-report=term-missing"])

        if pattern:
            cmd.extend(["-k", pattern])

        cmd.append(test_path)

        # Execute tests
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.max_execution_time,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(
                    f"Tests timed out after {self.config.max_execution_time}s"
                )

            duration_ms = (time.time() - start_time) * 1000
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Parse test results from output
            passed = stdout_str.count(" passed")
            failed = stdout_str.count(" failed")
            errors = stdout_str.count(" error")
            skipped = stdout_str.count(" skipped")

            return {
                "stdout": stdout_str,
                "stderr": stderr_str,
                "return_code": process.returncode or 0,
                "duration_ms": duration_ms,
                "success": process.returncode == 0,
                "summary": {
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "skipped": skipped,
                },
            }

        except Exception as e:
            return {
                "error": str(e),
                "success": False,
            }

    async def _analyze_code(
        self,
        code: str | None = None,
        file_path: str | None = None,
        checks: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze code quality.

        Args:
            code: Code string to analyze
            file_path: Path to file to analyze
            checks: List of checks to run (lint, type, security)

        Returns:
            Analysis results
        """
        checks = checks or ["lint"]
        results: dict[str, Any] = {"checks": {}}

        # Prepare code
        if code:
            if not self._temp_dir:
                self._temp_dir = Path(tempfile.mkdtemp(prefix="paracle_meta_"))
            file_path = str(self._temp_dir / "analyze.py")
            Path(file_path).write_text(code, encoding="utf-8")

        if not file_path:
            raise ValueError("Either 'code' or 'file_path' must be provided")

        # Run linting with ruff
        if "lint" in checks:
            results["checks"]["lint"] = await self._run_ruff(file_path)

        # Run type checking with mypy
        if "type" in checks:
            results["checks"]["type"] = await self._run_mypy(file_path)

        # Clean up if we created temp file
        if code and self._temp_dir:
            Path(file_path).unlink(missing_ok=True)

        # Overall success
        results["success"] = all(
            check.get("success", False) for check in results["checks"].values()
        )

        return results

    async def _run_ruff(self, file_path: str) -> dict[str, Any]:
        """Run ruff linter on code."""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "ruff",
                "check",
                file_path,
                "--output-format=json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)

            import json

            try:
                issues = json.loads(stdout.decode())
            except json.JSONDecodeError:
                issues = []

            return {
                "success": process.returncode == 0,
                "issues": issues,
                "issue_count": len(issues),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_mypy(self, file_path: str) -> dict[str, Any]:
        """Run mypy type checker on code."""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "mypy",
                file_path,
                "--ignore-missing-imports",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)

            output = stdout.decode("utf-8", errors="replace")
            issues = [line for line in output.split("\n") if line and "error:" in line]

            return {
                "success": process.returncode == 0,
                "output": output,
                "issues": issues,
                "issue_count": len(issues),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _install_packages(
        self,
        packages: list[str],
        upgrade: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """Install Python packages.

        Args:
            packages: List of packages to install
            upgrade: Upgrade existing packages

        Returns:
            Installation result
        """
        if not self.config.install_packages:
            raise PermissionError("Package installation is disabled")

        # Build pip command
        cmd = [sys.executable, "-m", "pip", "install"]

        if upgrade:
            cmd.append("--upgrade")

        cmd.extend(packages)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=120.0
            )

            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "packages": packages,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "packages": packages,
            }

    # Convenience methods
    async def run_python(self, code: str, **kwargs) -> CapabilityResult:
        """Execute Python code."""
        return await self.execute(action="run", code=code, language="python", **kwargs)

    async def run_tests(
        self, test_path: str = "tests/", coverage: bool = False
    ) -> CapabilityResult:
        """Run pytest tests."""
        return await self.execute(action="test", test_path=test_path, coverage=coverage)

    async def analyze(
        self, code: str, checks: list[str] | None = None
    ) -> CapabilityResult:
        """Analyze code quality."""
        return await self.execute(action="analyze", code=code, checks=checks)
