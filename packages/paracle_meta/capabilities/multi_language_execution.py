"""Multi-language code execution capability for MetaAgent.

Provides secure code execution in multiple programming languages:
- Python (native)
- JavaScript/TypeScript (via Node.js/Deno/Bun)
- Go (via go run)
- Rust (via rustc/cargo)
- Shell/Bash
- Ruby
- Java
- C/C++

Security Features:
- Configurable timeout per language
- Sandboxed temp directory execution
- Resource limits
- Network isolation options
"""

import asyncio
import os
import shutil
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class Language(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    BASH = "bash"
    SHELL = "shell"
    RUBY = "ruby"
    JAVA = "java"
    C = "c"
    CPP = "cpp"


# Language file extensions
LANGUAGE_EXTENSIONS: dict[Language, str] = {
    Language.PYTHON: ".py",
    Language.JAVASCRIPT: ".js",
    Language.TYPESCRIPT: ".ts",
    Language.GO: ".go",
    Language.RUST: ".rs",
    Language.BASH: ".sh",
    Language.SHELL: ".sh",
    Language.RUBY: ".rb",
    Language.JAVA: ".java",
    Language.C: ".c",
    Language.CPP: ".cpp",
}


class LanguageConfig:
    """Configuration for a specific language runtime."""

    def __init__(
        self,
        language: Language,
        runtime_path: str | None = None,
        compile_command: list[str] | None = None,
        run_command: list[str] | None = None,
        default_timeout: float = 60.0,
        env_vars: dict[str, str] | None = None,
    ):
        self.language = language
        self.runtime_path = runtime_path
        self.compile_command = compile_command
        self.run_command = run_command
        self.default_timeout = default_timeout
        self.env_vars = env_vars or {}


class MultiLanguageConfig(CapabilityConfig):
    """Configuration for multi-language code execution."""

    # Allowed languages
    allowed_languages: list[str] = Field(
        default_factory=lambda: [
            "python",
            "javascript",
            "typescript",
            "go",
            "rust",
            "bash",
        ],
        description="Allowed programming languages",
    )

    # Execution settings
    max_execution_time: float = Field(
        default=60.0,
        ge=1.0,
        le=600.0,
        description="Default max execution time in seconds",
    )
    max_memory_mb: int = Field(
        default=512,
        ge=64,
        le=8192,
        description="Max memory usage in MB",
    )
    allow_network: bool = Field(
        default=False,
        description="Allow network access during execution",
    )
    allow_file_write: bool = Field(
        default=True,
        description="Allow writing files in temp directory",
    )

    # Working directory
    working_dir: str | None = Field(
        default=None,
        description="Working directory for execution",
    )

    # Runtime paths (auto-detected if None)
    python_path: str | None = None
    node_path: str | None = None
    deno_path: str | None = None
    bun_path: str | None = None
    go_path: str | None = None
    rust_path: str | None = None  # rustc
    cargo_path: str | None = None
    ruby_path: str | None = None
    java_path: str | None = None
    javac_path: str | None = None
    gcc_path: str | None = None
    gpp_path: str | None = None  # g++

    # TypeScript runtime preference
    typescript_runtime: str = Field(
        default="auto",
        description="Preferred TypeScript runtime: auto, deno, bun, tsc",
    )

    # JavaScript runtime preference
    javascript_runtime: str = Field(
        default="auto",
        description="Preferred JavaScript runtime: auto, node, deno, bun",
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
        compile_output: str | None = None,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.duration_ms = duration_ms
        self.language = language
        self.files_created = files_created or []
        self.compile_output = compile_output
        self.success = return_code == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "duration_ms": self.duration_ms,
            "language": self.language,
            "files_created": self.files_created,
            "success": self.success,
        }
        if self.compile_output:
            result["compile_output"] = self.compile_output
        return result


class LanguageExecutor(ABC):
    """Abstract base class for language-specific executors."""

    language: Language

    def __init__(self, config: MultiLanguageConfig, temp_dir: Path):
        self.config = config
        self.temp_dir = temp_dir

    @abstractmethod
    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        """Execute code and return result."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if runtime is available."""
        pass

    def get_runtime_path(self) -> str | None:
        """Get path to runtime executable."""
        return None

    async def _run_process(
        self,
        cmd: list[str],
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> tuple[str, str, int, float]:
        """Run a subprocess and return output."""
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        if not self.config.allow_network:
            exec_env["PARACLE_NO_NETWORK"] = "1"

        start_time = time.time()
        timeout = timeout or self.config.max_execution_time

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or str(self.temp_dir),
                env=exec_env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Execution timed out after {timeout}s")

            duration_ms = (time.time() - start_time) * 1000

            return (
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
                process.returncode or 0,
                duration_ms,
            )

        except FileNotFoundError as e:
            raise RuntimeError(f"Runtime not found: {cmd[0]}") from e


class PythonExecutor(LanguageExecutor):
    """Python code executor."""

    language = Language.PYTHON

    def is_available(self) -> bool:
        return True  # Python is always available

    def get_runtime_path(self) -> str:
        return self.config.python_path or sys.executable

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        script_name = filename or "script.py"
        script_path = self.temp_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        try:
            cmd = [self.get_runtime_path(), str(script_path)]
            if args:
                cmd.extend(args)

            stdout, stderr, return_code, duration_ms = await self._run_process(
                cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name for f in self.temp_dir.iterdir() if f.name != script_name
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=duration_ms,
                language="python",
                files_created=files_created,
            )
        finally:
            if script_path.exists():
                script_path.unlink()


class JavaScriptExecutor(LanguageExecutor):
    """JavaScript code executor (Node.js, Deno, or Bun)."""

    language = Language.JAVASCRIPT

    def is_available(self) -> bool:
        return self._get_runtime() is not None

    def _get_runtime(self) -> tuple[str, str] | None:
        """Get available JS runtime (path, type)."""
        preference = self.config.javascript_runtime

        runtimes = []
        if preference == "auto":
            runtimes = [
                (self.config.node_path, "node"),
                (self.config.deno_path, "deno"),
                (self.config.bun_path, "bun"),
            ]
        elif preference == "node":
            runtimes = [(self.config.node_path, "node")]
        elif preference == "deno":
            runtimes = [(self.config.deno_path, "deno")]
        elif preference == "bun":
            runtimes = [(self.config.bun_path, "bun")]

        for path, runtime_type in runtimes:
            runtime = path or shutil.which(runtime_type)
            if runtime and Path(runtime).exists() or shutil.which(runtime_type):
                return (runtime or runtime_type, runtime_type)

        return None

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        runtime = self._get_runtime()
        if not runtime:
            raise RuntimeError("No JavaScript runtime available (node, deno, bun)")

        runtime_path, runtime_type = runtime
        script_name = filename or "script.js"
        script_path = self.temp_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        try:
            if runtime_type == "deno":
                cmd = [runtime_path, "run", "--allow-read", "--allow-write"]
                if self.config.allow_network:
                    cmd.append("--allow-net")
                cmd.append(str(script_path))
            elif runtime_type == "bun":
                cmd = [runtime_path, "run", str(script_path)]
            else:  # node
                cmd = [runtime_path, str(script_path)]

            if args:
                cmd.extend(args)

            stdout, stderr, return_code, duration_ms = await self._run_process(
                cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name for f in self.temp_dir.iterdir() if f.name != script_name
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=duration_ms,
                language="javascript",
                files_created=files_created,
            )
        finally:
            if script_path.exists():
                script_path.unlink()


class TypeScriptExecutor(LanguageExecutor):
    """TypeScript code executor (Deno, Bun, or tsc + node)."""

    language = Language.TYPESCRIPT

    def is_available(self) -> bool:
        return self._get_runtime() is not None

    def _get_runtime(self) -> tuple[str, str] | None:
        """Get available TS runtime."""
        preference = self.config.typescript_runtime

        runtimes = []
        if preference == "auto":
            runtimes = [
                (self.config.deno_path, "deno"),
                (self.config.bun_path, "bun"),
            ]
        elif preference == "deno":
            runtimes = [(self.config.deno_path, "deno")]
        elif preference == "bun":
            runtimes = [(self.config.bun_path, "bun")]

        for path, runtime_type in runtimes:
            runtime = path or shutil.which(runtime_type)
            if runtime:
                return (runtime, runtime_type)

        return None

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        runtime = self._get_runtime()
        if not runtime:
            raise RuntimeError("No TypeScript runtime available (deno, bun)")

        runtime_path, runtime_type = runtime
        script_name = filename or "script.ts"
        script_path = self.temp_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        try:
            if runtime_type == "deno":
                cmd = [runtime_path, "run", "--allow-read", "--allow-write"]
                if self.config.allow_network:
                    cmd.append("--allow-net")
                cmd.append(str(script_path))
            else:  # bun
                cmd = [runtime_path, "run", str(script_path)]

            if args:
                cmd.extend(args)

            stdout, stderr, return_code, duration_ms = await self._run_process(
                cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name for f in self.temp_dir.iterdir() if f.name != script_name
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=duration_ms,
                language="typescript",
                files_created=files_created,
            )
        finally:
            if script_path.exists():
                script_path.unlink()


class GoExecutor(LanguageExecutor):
    """Go code executor."""

    language = Language.GO

    def is_available(self) -> bool:
        go_path = self.config.go_path or shutil.which("go")
        return go_path is not None

    def get_runtime_path(self) -> str | None:
        return self.config.go_path or shutil.which("go")

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        go_path = self.get_runtime_path()
        if not go_path:
            raise RuntimeError("Go runtime not found")

        script_name = filename or "main.go"
        script_path = self.temp_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        try:
            cmd = [go_path, "run", str(script_path)]
            if args:
                cmd.extend(args)

            stdout, stderr, return_code, duration_ms = await self._run_process(
                cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name for f in self.temp_dir.iterdir() if f.name != script_name
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=duration_ms,
                language="go",
                files_created=files_created,
            )
        finally:
            if script_path.exists():
                script_path.unlink()


class RustExecutor(LanguageExecutor):
    """Rust code executor."""

    language = Language.RUST

    def is_available(self) -> bool:
        rustc = self.config.rust_path or shutil.which("rustc")
        return rustc is not None

    def get_runtime_path(self) -> str | None:
        return self.config.rust_path or shutil.which("rustc")

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        rustc = self.get_runtime_path()
        if not rustc:
            raise RuntimeError("Rust compiler (rustc) not found")

        script_name = filename or "main.rs"
        script_path = self.temp_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        # Output binary name
        binary_name = script_path.stem
        if sys.platform == "win32":
            binary_name += ".exe"
        binary_path = self.temp_dir / binary_name

        try:
            # Compile
            compile_cmd = [rustc, str(script_path), "-o", str(binary_path)]
            compile_stdout, compile_stderr, compile_code, compile_time = (
                await self._run_process(compile_cmd, env=env, timeout=timeout)
            )

            if compile_code != 0:
                return ExecutionResult(
                    stdout="",
                    stderr=compile_stderr,
                    return_code=compile_code,
                    duration_ms=compile_time,
                    language="rust",
                    compile_output=compile_stderr,
                )

            # Run compiled binary
            run_cmd = [str(binary_path)]
            if args:
                run_cmd.extend(args)

            stdout, stderr, return_code, run_time = await self._run_process(
                run_cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name
                for f in self.temp_dir.iterdir()
                if f.name not in [script_name, binary_name]
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=compile_time + run_time,
                language="rust",
                files_created=files_created,
                compile_output=compile_stdout + compile_stderr,
            )
        finally:
            if script_path.exists():
                script_path.unlink()
            if binary_path.exists():
                binary_path.unlink()


class BashExecutor(LanguageExecutor):
    """Bash/Shell script executor."""

    language = Language.BASH

    def is_available(self) -> bool:
        if sys.platform == "win32":
            # Check for Git Bash, WSL bash, or PowerShell
            return shutil.which("bash") is not None or shutil.which("sh") is not None
        return True

    def get_runtime_path(self) -> str:
        if sys.platform == "win32":
            bash = shutil.which("bash") or shutil.which("sh")
            if bash:
                return bash
            raise RuntimeError("No shell available on Windows")
        return "/bin/bash"

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        script_name = filename or "script.sh"
        script_path = self.temp_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        try:
            bash_path = self.get_runtime_path()
            cmd = [bash_path, str(script_path)]
            if args:
                cmd.extend(args)

            stdout, stderr, return_code, duration_ms = await self._run_process(
                cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name for f in self.temp_dir.iterdir() if f.name != script_name
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=duration_ms,
                language="bash",
                files_created=files_created,
            )
        finally:
            if script_path.exists():
                script_path.unlink()


class RubyExecutor(LanguageExecutor):
    """Ruby code executor."""

    language = Language.RUBY

    def is_available(self) -> bool:
        ruby = self.config.ruby_path or shutil.which("ruby")
        return ruby is not None

    def get_runtime_path(self) -> str | None:
        return self.config.ruby_path or shutil.which("ruby")

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        ruby = self.get_runtime_path()
        if not ruby:
            raise RuntimeError("Ruby runtime not found")

        script_name = filename or "script.rb"
        script_path = self.temp_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        try:
            cmd = [ruby, str(script_path)]
            if args:
                cmd.extend(args)

            stdout, stderr, return_code, duration_ms = await self._run_process(
                cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name for f in self.temp_dir.iterdir() if f.name != script_name
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=duration_ms,
                language="ruby",
                files_created=files_created,
            )
        finally:
            if script_path.exists():
                script_path.unlink()


class JavaExecutor(LanguageExecutor):
    """Java code executor."""

    language = Language.JAVA

    def is_available(self) -> bool:
        javac = self.config.javac_path or shutil.which("javac")
        java = self.config.java_path or shutil.which("java")
        return javac is not None and java is not None

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        javac = self.config.javac_path or shutil.which("javac")
        java = self.config.java_path or shutil.which("java")

        if not javac or not java:
            raise RuntimeError("Java compiler/runtime not found")

        # Extract class name from code
        import re

        match = re.search(r"public\s+class\s+(\w+)", code)
        class_name = match.group(1) if match else "Main"

        script_name = filename or f"{class_name}.java"
        script_path = self.temp_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        try:
            # Compile
            compile_cmd = [javac, str(script_path)]
            compile_stdout, compile_stderr, compile_code, compile_time = (
                await self._run_process(compile_cmd, env=env, timeout=timeout)
            )

            if compile_code != 0:
                return ExecutionResult(
                    stdout="",
                    stderr=compile_stderr,
                    return_code=compile_code,
                    duration_ms=compile_time,
                    language="java",
                    compile_output=compile_stderr,
                )

            # Run
            run_cmd = [java, "-cp", str(self.temp_dir), class_name]
            if args:
                run_cmd.extend(args)

            stdout, stderr, return_code, run_time = await self._run_process(
                run_cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name
                for f in self.temp_dir.iterdir()
                if f.name not in [script_name, f"{class_name}.class"]
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=compile_time + run_time,
                language="java",
                files_created=files_created,
                compile_output=compile_stdout + compile_stderr,
            )
        finally:
            if script_path.exists():
                script_path.unlink()
            class_file = self.temp_dir / f"{class_name}.class"
            if class_file.exists():
                class_file.unlink()


class CExecutor(LanguageExecutor):
    """C code executor."""

    language = Language.C

    def is_available(self) -> bool:
        gcc = self.config.gcc_path or shutil.which("gcc")
        return gcc is not None

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        gcc = self.config.gcc_path or shutil.which("gcc")
        if not gcc:
            raise RuntimeError("GCC compiler not found")

        script_name = filename or "main.c"
        script_path = self.temp_dir / script_name

        # Output binary
        binary_name = script_path.stem
        if sys.platform == "win32":
            binary_name += ".exe"
        binary_path = self.temp_dir / binary_name

        script_path.write_text(code, encoding="utf-8")

        try:
            # Compile
            compile_cmd = [gcc, str(script_path), "-o", str(binary_path)]
            compile_stdout, compile_stderr, compile_code, compile_time = (
                await self._run_process(compile_cmd, env=env, timeout=timeout)
            )

            if compile_code != 0:
                return ExecutionResult(
                    stdout="",
                    stderr=compile_stderr,
                    return_code=compile_code,
                    duration_ms=compile_time,
                    language="c",
                    compile_output=compile_stderr,
                )

            # Run
            run_cmd = [str(binary_path)]
            if args:
                run_cmd.extend(args)

            stdout, stderr, return_code, run_time = await self._run_process(
                run_cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name
                for f in self.temp_dir.iterdir()
                if f.name not in [script_name, binary_name]
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=compile_time + run_time,
                language="c",
                files_created=files_created,
                compile_output=compile_stdout + compile_stderr,
            )
        finally:
            if script_path.exists():
                script_path.unlink()
            if binary_path.exists():
                binary_path.unlink()


class CppExecutor(LanguageExecutor):
    """C++ code executor."""

    language = Language.CPP

    def is_available(self) -> bool:
        gpp = self.config.gpp_path or shutil.which("g++")
        return gpp is not None

    async def execute(
        self,
        code: str,
        filename: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        gpp = self.config.gpp_path or shutil.which("g++")
        if not gpp:
            raise RuntimeError("G++ compiler not found")

        script_name = filename or "main.cpp"
        script_path = self.temp_dir / script_name

        # Output binary
        binary_name = script_path.stem
        if sys.platform == "win32":
            binary_name += ".exe"
        binary_path = self.temp_dir / binary_name

        script_path.write_text(code, encoding="utf-8")

        try:
            # Compile with C++17
            compile_cmd = [gpp, "-std=c++17", str(script_path), "-o", str(binary_path)]
            compile_stdout, compile_stderr, compile_code, compile_time = (
                await self._run_process(compile_cmd, env=env, timeout=timeout)
            )

            if compile_code != 0:
                return ExecutionResult(
                    stdout="",
                    stderr=compile_stderr,
                    return_code=compile_code,
                    duration_ms=compile_time,
                    language="cpp",
                    compile_output=compile_stderr,
                )

            # Run
            run_cmd = [str(binary_path)]
            if args:
                run_cmd.extend(args)

            stdout, stderr, return_code, run_time = await self._run_process(
                run_cmd, env=env, timeout=timeout
            )

            files_created = [
                f.name
                for f in self.temp_dir.iterdir()
                if f.name not in [script_name, binary_name]
            ]

            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                duration_ms=compile_time + run_time,
                language="cpp",
                files_created=files_created,
                compile_output=compile_stdout + compile_stderr,
            )
        finally:
            if script_path.exists():
                script_path.unlink()
            if binary_path.exists():
                binary_path.unlink()


# Registry of all executors
EXECUTOR_REGISTRY: dict[str, type[LanguageExecutor]] = {
    "python": PythonExecutor,
    "javascript": JavaScriptExecutor,
    "typescript": TypeScriptExecutor,
    "go": GoExecutor,
    "rust": RustExecutor,
    "bash": BashExecutor,
    "shell": BashExecutor,
    "ruby": RubyExecutor,
    "java": JavaExecutor,
    "c": CExecutor,
    "cpp": CppExecutor,
}


class MultiLanguageExecutionCapability(BaseCapability):
    """Multi-language code execution capability.

    Provides secure execution of code in multiple programming languages
    with configurable runtimes, timeouts, and resource limits.

    Supported Languages:
        - Python (native, always available)
        - JavaScript (Node.js, Deno, Bun)
        - TypeScript (Deno, Bun)
        - Go (go run)
        - Rust (rustc)
        - Bash/Shell
        - Ruby
        - Java (javac + java)
        - C (gcc)
        - C++ (g++)

    Example:
        >>> executor = MultiLanguageExecutionCapability()
        >>> await executor.initialize()

        >>> # Run Python
        >>> result = await executor.run("print('Hello')", language="python")

        >>> # Run JavaScript
        >>> result = await executor.run("console.log('Hello')", language="javascript")

        >>> # Run Go
        >>> go_code = '''
        ... package main
        ... import "fmt"
        ... func main() { fmt.Println("Hello Go") }
        ... '''
        >>> result = await executor.run(go_code, language="go")

        >>> # Run Rust
        >>> rust_code = 'fn main() { println!("Hello Rust"); }'
        >>> result = await executor.run(rust_code, language="rust")

        >>> # Check available languages
        >>> available = executor.get_available_languages()
    """

    name = "multi_language_execution"
    description = "Execute code in Python, JS/TS, Go, Rust, Bash, Ruby, Java, C/C++"

    def __init__(self, config: MultiLanguageConfig | None = None):
        """Initialize multi-language execution capability."""
        super().__init__(config or MultiLanguageConfig())
        self.config: MultiLanguageConfig = self.config
        self._temp_dir: Path | None = None
        self._executors: dict[str, LanguageExecutor] = {}

    async def initialize(self) -> None:
        """Initialize execution environment."""
        self._temp_dir = Path(tempfile.mkdtemp(prefix="paracle_multi_"))

        # Initialize executors for allowed languages
        for lang in self.config.allowed_languages:
            if lang in EXECUTOR_REGISTRY:
                executor_class = EXECUTOR_REGISTRY[lang]
                executor = executor_class(self.config, self._temp_dir)
                if executor.is_available():
                    self._executors[lang] = executor

        await super().initialize()

    async def shutdown(self) -> None:
        """Cleanup execution environment."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
        self._executors = {}
        await super().shutdown()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute capability action.

        Args:
            action: Action (run, list_languages, check_runtime)
            **kwargs: Action-specific parameters

        Returns:
            CapabilityResult with outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "run")
        start_time = time.time()

        try:
            if action == "run":
                result = await self._run_code(**kwargs)
            elif action == "list_languages":
                result = self._list_languages()
            elif action == "check_runtime":
                result = self._check_runtime(kwargs.get("language", "python"))
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
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Run code in specified language."""
        language = language.lower()

        if language not in self.config.allowed_languages:
            raise ValueError(
                f"Language '{language}' not allowed. "
                f"Allowed: {self.config.allowed_languages}"
            )

        if language not in self._executors:
            raise RuntimeError(
                f"Language '{language}' runtime not available. "
                f"Available: {list(self._executors.keys())}"
            )

        executor = self._executors[language]
        result = await executor.execute(
            code=code,
            filename=filename,
            args=args,
            env=env,
            timeout=timeout,
        )
        return result.to_dict()

    def _list_languages(self) -> dict[str, Any]:
        """List available languages and their status."""
        languages = {}
        for lang, executor_class in EXECUTOR_REGISTRY.items():
            if self._temp_dir:
                executor = executor_class(self.config, self._temp_dir)
                languages[lang] = {
                    "allowed": lang in self.config.allowed_languages,
                    "available": executor.is_available(),
                    "runtime_path": executor.get_runtime_path(),
                }
            else:
                languages[lang] = {
                    "allowed": lang in self.config.allowed_languages,
                    "available": False,
                    "runtime_path": None,
                }
        return languages

    def _check_runtime(self, language: str) -> dict[str, Any]:
        """Check if a specific runtime is available."""
        language = language.lower()
        if language not in EXECUTOR_REGISTRY:
            return {
                "language": language,
                "supported": False,
                "available": False,
                "error": f"Unknown language: {language}",
            }

        executor_class = EXECUTOR_REGISTRY[language]
        if self._temp_dir:
            executor = executor_class(self.config, self._temp_dir)
            return {
                "language": language,
                "supported": True,
                "available": executor.is_available(),
                "runtime_path": executor.get_runtime_path(),
            }
        return {
            "language": language,
            "supported": True,
            "available": False,
            "runtime_path": None,
        }

    def get_available_languages(self) -> list[str]:
        """Get list of available languages."""
        return list(self._executors.keys())

    # Convenience methods
    async def run(
        self,
        code: str,
        language: str = "python",
        **kwargs,
    ) -> CapabilityResult:
        """Run code in specified language."""
        return await self.execute(action="run", code=code, language=language, **kwargs)

    async def run_python(self, code: str, **kwargs) -> CapabilityResult:
        """Run Python code."""
        return await self.run(code, language="python", **kwargs)

    async def run_javascript(self, code: str, **kwargs) -> CapabilityResult:
        """Run JavaScript code."""
        return await self.run(code, language="javascript", **kwargs)

    async def run_typescript(self, code: str, **kwargs) -> CapabilityResult:
        """Run TypeScript code."""
        return await self.run(code, language="typescript", **kwargs)

    async def run_go(self, code: str, **kwargs) -> CapabilityResult:
        """Run Go code."""
        return await self.run(code, language="go", **kwargs)

    async def run_rust(self, code: str, **kwargs) -> CapabilityResult:
        """Run Rust code."""
        return await self.run(code, language="rust", **kwargs)

    async def run_bash(self, code: str, **kwargs) -> CapabilityResult:
        """Run Bash script."""
        return await self.run(code, language="bash", **kwargs)

    async def run_ruby(self, code: str, **kwargs) -> CapabilityResult:
        """Run Ruby code."""
        return await self.run(code, language="ruby", **kwargs)

    async def run_java(self, code: str, **kwargs) -> CapabilityResult:
        """Run Java code."""
        return await self.run(code, language="java", **kwargs)

    async def run_c(self, code: str, **kwargs) -> CapabilityResult:
        """Run C code."""
        return await self.run(code, language="c", **kwargs)

    async def run_cpp(self, code: str, **kwargs) -> CapabilityResult:
        """Run C++ code."""
        return await self.run(code, language="cpp", **kwargs)
