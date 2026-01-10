"""
Polyglot Capability - Multi-language extension system.

Allows implementing paracle_meta features in Go, Rust, JavaScript/TypeScript.
Extensions communicate via JSON-RPC, gRPC, or MessagePack protocols.

Supports:
- Go binaries with JSON-RPC
- Rust binaries (native or via PyO3)
- JavaScript/TypeScript via Node.js or Deno
- WebAssembly modules
- Hot-reload of extensions
"""

import asyncio
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .base import BaseCapability, CapabilityResult


class ExtensionLanguage(str, Enum):
    """Supported extension languages."""

    GO = "go"
    RUST = "rust"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    WASM = "wasm"
    PYTHON = "python"  # For consistency


class Protocol(str, Enum):
    """Communication protocols for extensions."""

    JSON_RPC = "json-rpc"
    JSON_LINES = "json-lines"  # Simple newline-delimited JSON
    MSGPACK = "msgpack"
    GRPC = "grpc"


class ExtensionStatus(str, Enum):
    """Extension runtime status."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    RELOADING = "reloading"


@dataclass
class ExtensionManifest:
    """Extension manifest defining capabilities and metadata."""

    name: str
    version: str
    language: ExtensionLanguage
    description: str = ""
    author: str = ""
    protocol: Protocol = Protocol.JSON_LINES
    entry_point: str = ""  # Main file or binary
    build_command: str | None = None  # Command to build the extension
    methods: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtensionManifest":
        """Create manifest from dictionary."""
        return cls(
            name=data["name"],
            version=data.get("version", "0.0.1"),
            language=ExtensionLanguage(data["language"]),
            description=data.get("description", ""),
            author=data.get("author", ""),
            protocol=Protocol(data.get("protocol", "json-lines")),
            entry_point=data.get("entry_point", ""),
            build_command=data.get("build_command"),
            methods=data.get("methods", []),
            dependencies=data.get("dependencies", []),
            config_schema=data.get("config_schema", {}),
        )


@dataclass
class ExtensionInfo:
    """Runtime information about an extension."""

    manifest: ExtensionManifest
    path: Path
    status: ExtensionStatus = ExtensionStatus.STOPPED
    process: asyncio.subprocess.Process | None = None
    pid: int | None = None
    started_at: datetime | None = None
    call_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    binary_path: Path | None = None


@dataclass
class PolyglotConfig:
    """Configuration for polyglot capability."""

    # Extension directories
    extensions_dir: str = "./extensions"
    cache_dir: str | None = None  # For compiled binaries

    # Protocol settings
    default_protocol: Protocol = Protocol.JSON_LINES
    request_timeout: int = 30  # seconds

    # Process management
    max_concurrent_extensions: int = 10
    auto_restart: bool = True
    restart_delay: float = 1.0  # seconds
    max_restart_attempts: int = 3

    # Hot reload
    enable_hot_reload: bool = True
    watch_interval: float = 2.0  # seconds

    # Build settings
    auto_build: bool = True
    go_path: str | None = None
    rust_target: str = "release"
    node_path: str | None = None
    deno_path: str | None = None


class ExtensionRunner(ABC):
    """Abstract base for language-specific extension runners."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if runtime is available."""
        pass

    @abstractmethod
    async def build(self, extension: ExtensionInfo) -> Path:
        """Build extension and return binary/entry path."""
        pass

    @abstractmethod
    async def start(self, extension: ExtensionInfo) -> asyncio.subprocess.Process:
        """Start extension process."""
        pass

    @abstractmethod
    async def call(
        self,
        extension: ExtensionInfo,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Call extension method."""
        pass


class GoRunner(ExtensionRunner):
    """Runner for Go extensions."""

    def __init__(self, config: PolyglotConfig):
        self.config = config
        self._go_path: str | None = None

    async def is_available(self) -> bool:
        """Check if Go is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "go", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
        except FileNotFoundError:
            return False

    async def build(self, extension: ExtensionInfo) -> Path:
        """Build Go extension."""
        ext_path = extension.path
        manifest = extension.manifest

        # Determine output path
        cache_dir = Path(self.config.cache_dir or tempfile.gettempdir()) / "paracle_extensions"
        cache_dir.mkdir(parents=True, exist_ok=True)

        binary_name = f"{manifest.name}"
        if sys.platform == "win32":
            binary_name += ".exe"

        binary_path = cache_dir / binary_name

        # Check if rebuild needed
        source_hash = await self._hash_sources(ext_path)
        hash_file = cache_dir / f"{manifest.name}.hash"

        if binary_path.exists() and hash_file.exists():
            existing_hash = hash_file.read_text().strip()
            if existing_hash == source_hash:
                return binary_path

        # Build - always use the full binary path
        build_cmd = f"go build -o \"{binary_path}\""

        proc = await asyncio.create_subprocess_shell(
            build_cmd,
            cwd=str(ext_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"Go build failed: {stderr.decode()}")

        # Save hash
        hash_file.write_text(source_hash)

        return binary_path

    async def _hash_sources(self, path: Path) -> str:
        """Hash all source files for cache invalidation."""
        hasher = hashlib.sha256()
        for go_file in sorted(path.rglob("*.go")):
            hasher.update(go_file.read_bytes())
        return hasher.hexdigest()

    async def start(self, extension: ExtensionInfo) -> asyncio.subprocess.Process:
        """Start Go extension process."""
        if not extension.binary_path:
            extension.binary_path = await self.build(extension)

        proc = await asyncio.create_subprocess_exec(
            str(extension.binary_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return proc

    async def call(
        self,
        extension: ExtensionInfo,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Call Go extension method."""
        if not extension.process or extension.process.returncode is not None:
            raise RuntimeError("Extension process not running")

        # JSON-Lines protocol
        request = json.dumps({"method": method, "params": params}) + "\n"
        extension.process.stdin.write(request.encode())
        await extension.process.stdin.drain()

        # Read response
        response_line = await asyncio.wait_for(
            extension.process.stdout.readline(),
            timeout=self.config.request_timeout,
        )

        return json.loads(response_line.decode())


class RustRunner(ExtensionRunner):
    """Runner for Rust extensions."""

    def __init__(self, config: PolyglotConfig):
        self.config = config

    async def is_available(self) -> bool:
        """Check if Rust/Cargo is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "cargo", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
        except FileNotFoundError:
            return False

    async def build(self, extension: ExtensionInfo) -> Path:
        """Build Rust extension."""
        ext_path = extension.path
        manifest = extension.manifest

        # Build with cargo
        build_mode = "--release" if self.config.rust_target == "release" else ""
        build_cmd = manifest.build_command or f"cargo build {build_mode}"

        proc = await asyncio.create_subprocess_shell(
            build_cmd,
            cwd=str(ext_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"Rust build failed: {stderr.decode()}")

        # Find binary
        target_dir = ext_path / "target" / self.config.rust_target
        binary_name = manifest.name
        if sys.platform == "win32":
            binary_name += ".exe"

        binary_path = target_dir / binary_name
        if not binary_path.exists():
            # Try to find it
            for f in target_dir.iterdir():
                if f.is_file() and f.suffix in ("", ".exe") and f.stem == manifest.name:
                    binary_path = f
                    break

        return binary_path

    async def start(self, extension: ExtensionInfo) -> asyncio.subprocess.Process:
        """Start Rust extension process."""
        if not extension.binary_path:
            extension.binary_path = await self.build(extension)

        proc = await asyncio.create_subprocess_exec(
            str(extension.binary_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return proc

    async def call(
        self,
        extension: ExtensionInfo,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Call Rust extension method."""
        if not extension.process or extension.process.returncode is not None:
            raise RuntimeError("Extension process not running")

        request = json.dumps({"method": method, "params": params}) + "\n"
        extension.process.stdin.write(request.encode())
        await extension.process.stdin.drain()

        response_line = await asyncio.wait_for(
            extension.process.stdout.readline(),
            timeout=self.config.request_timeout,
        )

        return json.loads(response_line.decode())


class JavaScriptRunner(ExtensionRunner):
    """Runner for JavaScript/TypeScript extensions."""

    def __init__(self, config: PolyglotConfig, use_deno: bool = False):
        self.config = config
        self.use_deno = use_deno
        self._runtime: str | None = None

    async def is_available(self) -> bool:
        """Check if Node.js or Deno is available."""
        runtime = "deno" if self.use_deno else "node"
        try:
            proc = await asyncio.create_subprocess_exec(
                runtime, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode == 0:
                self._runtime = runtime
                return True
        except FileNotFoundError:
            pass

        # Try alternative
        alt_runtime = "node" if self.use_deno else "deno"
        try:
            proc = await asyncio.create_subprocess_exec(
                alt_runtime, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode == 0:
                self._runtime = alt_runtime
                return True
        except FileNotFoundError:
            pass

        return False

    async def build(self, extension: ExtensionInfo) -> Path:
        """Build/prepare JS extension."""
        ext_path = extension.path
        manifest = extension.manifest

        # For TypeScript, compile if needed
        if manifest.language == ExtensionLanguage.TYPESCRIPT:
            if self._runtime == "deno":
                # Deno handles TS natively
                pass
            else:
                # Use tsc or ts-node
                if manifest.build_command:
                    proc = await asyncio.create_subprocess_shell(
                        manifest.build_command,
                        cwd=str(ext_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await proc.communicate()

        # Return entry point
        entry = manifest.entry_point or "index.js"
        if manifest.language == ExtensionLanguage.TYPESCRIPT and self._runtime != "deno":
            entry = entry.replace(".ts", ".js")

        return ext_path / entry

    async def start(self, extension: ExtensionInfo) -> asyncio.subprocess.Process:
        """Start JS extension process."""
        if not extension.binary_path:
            extension.binary_path = await self.build(extension)

        if self._runtime == "deno":
            cmd = [
                "deno", "run",
                "--allow-read", "--allow-write", "--allow-net",
                str(extension.binary_path)
            ]
        else:
            # Node.js
            if extension.manifest.language == ExtensionLanguage.TYPESCRIPT:
                cmd = ["npx", "ts-node", str(extension.binary_path)]
            else:
                cmd = ["node", str(extension.binary_path)]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return proc

    async def call(
        self,
        extension: ExtensionInfo,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Call JS extension method."""
        if not extension.process or extension.process.returncode is not None:
            raise RuntimeError("Extension process not running")

        request = json.dumps({"method": method, "params": params}) + "\n"
        extension.process.stdin.write(request.encode())
        await extension.process.stdin.drain()

        response_line = await asyncio.wait_for(
            extension.process.stdout.readline(),
            timeout=self.config.request_timeout,
        )

        return json.loads(response_line.decode())


class WasmRunner(ExtensionRunner):
    """Runner for WebAssembly extensions."""

    def __init__(self, config: PolyglotConfig):
        self.config = config
        self._wasmtime_available = False
        self._wasmer_available = False

    async def is_available(self) -> bool:
        """Check if WASM runtime is available."""
        try:
            import wasmtime  # noqa: F401
            self._wasmtime_available = True
            return True
        except ImportError:
            pass

        try:
            import wasmer  # noqa: F401
            self._wasmer_available = True
            return True
        except ImportError:
            pass

        return False

    async def build(self, extension: ExtensionInfo) -> Path:
        """Build WASM extension."""
        ext_path = extension.path
        manifest = extension.manifest

        if manifest.build_command:
            proc = await asyncio.create_subprocess_shell(
                manifest.build_command,
                cwd=str(ext_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                raise RuntimeError(f"WASM build failed: {stderr.decode()}")

        # Find .wasm file
        wasm_file = manifest.entry_point or f"{manifest.name}.wasm"
        return ext_path / wasm_file

    async def start(self, extension: ExtensionInfo) -> asyncio.subprocess.Process:
        """WASM runs in-process, no subprocess needed."""
        # Load WASM module
        if not extension.binary_path:
            extension.binary_path = await self.build(extension)

        # WASM is loaded on-demand in call()
        return None

    async def call(
        self,
        extension: ExtensionInfo,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Call WASM extension method."""
        if not extension.binary_path or not extension.binary_path.exists():
            raise RuntimeError("WASM module not found")

        if self._wasmtime_available:
            return await self._call_wasmtime(extension, method, params)
        elif self._wasmer_available:
            return await self._call_wasmer(extension, method, params)
        else:
            raise RuntimeError("No WASM runtime available")

    async def _call_wasmtime(
        self,
        extension: ExtensionInfo,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Call using wasmtime."""
        import wasmtime

        loop = asyncio.get_event_loop()

        def run_wasm():
            engine = wasmtime.Engine()
            module = wasmtime.Module.from_file(engine, str(extension.binary_path))
            store = wasmtime.Store(engine)
            instance = wasmtime.Instance(store, module, [])

            # Get exported function
            func = instance.exports(store).get(method)
            if func is None:
                raise RuntimeError(f"Method {method} not found in WASM module")

            # Simple parameter passing via JSON
            params_json = json.dumps(params)
            # This is simplified - real implementation would need proper ABI
            result = func(store)

            return {"result": result}

        return await loop.run_in_executor(None, run_wasm)

    async def _call_wasmer(
        self,
        extension: ExtensionInfo,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Call using wasmer."""
        import wasmer

        loop = asyncio.get_event_loop()

        def run_wasm():
            wasm_bytes = extension.binary_path.read_bytes()
            store = wasmer.Store()
            module = wasmer.Module(store, wasm_bytes)
            instance = wasmer.Instance(module)

            func = getattr(instance.exports, method, None)
            if func is None:
                raise RuntimeError(f"Method {method} not found in WASM module")

            result = func()
            return {"result": result}

        return await loop.run_in_executor(None, run_wasm)


class PolyglotCapability(BaseCapability):
    """
    Multi-language extension capability for paracle_meta.

    Allows implementing features in Go, Rust, JavaScript/TypeScript, or WASM.
    Extensions communicate via JSON-based protocols.

    Example:
        capability = PolyglotCapability(config=PolyglotConfig(
            extensions_dir="./extensions",
            enable_hot_reload=True
        ))

        # Discover and load extensions
        await capability.discover()

        # Call a Go extension
        result = await capability.call("image-processor", "resize", {
            "image": "photo.jpg",
            "width": 800
        })

        # Call a Rust extension
        result = await capability.call("crypto-utils", "hash", {
            "data": "secret",
            "algorithm": "sha256"
        })

        # List available extensions
        extensions = await capability.list_extensions()

    Extension Structure:
        extensions/
        ├── my-go-extension/
        │   ├── manifest.json
        │   ├── main.go
        │   └── go.mod
        ├── my-rust-extension/
        │   ├── manifest.json
        │   ├── Cargo.toml
        │   └── src/
        │       └── main.rs
        └── my-js-extension/
            ├── manifest.json
            ├── package.json
            └── index.ts
    """

    name = "polyglot"
    description = "Multi-language extension system (Go, Rust, JS/TS, WASM)"

    def __init__(self, config: PolyglotConfig | None = None):
        """Initialize polyglot capability."""
        self.config = config or PolyglotConfig()
        self._extensions: dict[str, ExtensionInfo] = {}
        self._runners: dict[ExtensionLanguage, ExtensionRunner] = {}
        self._watch_task: asyncio.Task | None = None
        self._initialized = False

    async def _init_runners(self) -> None:
        """Initialize language runners."""
        if self._initialized:
            return

        self._runners = {
            ExtensionLanguage.GO: GoRunner(self.config),
            ExtensionLanguage.RUST: RustRunner(self.config),
            ExtensionLanguage.JAVASCRIPT: JavaScriptRunner(self.config, use_deno=False),
            ExtensionLanguage.TYPESCRIPT: JavaScriptRunner(self.config, use_deno=False),
            ExtensionLanguage.WASM: WasmRunner(self.config),
        }
        self._initialized = True

    @property
    def is_available(self) -> bool:
        """Check if any extension runtime is available."""
        return True  # Basic functionality always available

    async def discover(self) -> list[str]:
        """
        Discover extensions in the extensions directory.

        Returns:
            List of discovered extension names
        """
        await self._init_runners()

        ext_dir = Path(self.config.extensions_dir)
        if not ext_dir.exists():
            ext_dir.mkdir(parents=True, exist_ok=True)
            return []

        discovered = []

        for item in ext_dir.iterdir():
            if not item.is_dir():
                continue

            manifest_path = item / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                manifest_data = json.loads(manifest_path.read_text())
                manifest = ExtensionManifest.from_dict(manifest_data)

                self._extensions[manifest.name] = ExtensionInfo(
                    manifest=manifest,
                    path=item,
                    status=ExtensionStatus.STOPPED,
                )
                discovered.append(manifest.name)
            except Exception as e:
                print(f"Failed to load extension from {item}: {e}")

        return discovered

    async def start_extension(self, name: str) -> bool:
        """
        Start an extension process.

        Args:
            name: Extension name

        Returns:
            True if started successfully
        """
        if name not in self._extensions:
            raise ValueError(f"Extension not found: {name}")

        ext = self._extensions[name]
        runner = self._runners.get(ext.manifest.language)

        if not runner:
            raise RuntimeError(f"No runner for language: {ext.manifest.language}")

        if not await runner.is_available():
            raise RuntimeError(
                f"Runtime for {ext.manifest.language.value} not available"
            )

        ext.status = ExtensionStatus.STARTING

        try:
            # Build if needed
            if self.config.auto_build:
                ext.binary_path = await runner.build(ext)

            # Start process
            ext.process = await runner.start(ext)
            if ext.process:
                ext.pid = ext.process.pid
            ext.status = ExtensionStatus.RUNNING
            ext.started_at = datetime.now()

            return True
        except Exception as e:
            ext.status = ExtensionStatus.ERROR
            ext.last_error = str(e)
            raise

    async def stop_extension(self, name: str) -> bool:
        """
        Stop an extension process.

        Args:
            name: Extension name

        Returns:
            True if stopped successfully
        """
        if name not in self._extensions:
            return False

        ext = self._extensions[name]

        if ext.process and ext.process.returncode is None:
            ext.process.terminate()
            try:
                await asyncio.wait_for(ext.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                ext.process.kill()
                await ext.process.wait()

        ext.status = ExtensionStatus.STOPPED
        ext.process = None
        ext.pid = None

        return True

    async def call(
        self,
        extension_name: str,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> CapabilityResult:
        """
        Call a method on an extension.

        Args:
            extension_name: Name of the extension
            method: Method to call
            params: Parameters to pass

        Returns:
            CapabilityResult with method output
        """
        await self._init_runners()

        if extension_name not in self._extensions:
            return CapabilityResult(
                capability=self.name,
                success=False,
                output={"error": f"Extension not found: {extension_name}"},
                error=f"Extension not found: {extension_name}",
            )

        ext = self._extensions[extension_name]

        # Auto-start if not running
        if ext.status != ExtensionStatus.RUNNING:
            try:
                await self.start_extension(extension_name)
            except Exception as e:
                return CapabilityResult(
                    capability=self.name,
                    success=False,
                    output={"error": str(e)},
                    error=str(e),
                )

        runner = self._runners.get(ext.manifest.language)
        if not runner:
            return CapabilityResult(
                capability=self.name,
                success=False,
                output={"error": f"No runner for {ext.manifest.language}"},
                error=f"No runner for {ext.manifest.language}",
            )

        try:
            ext.call_count += 1
            result = await runner.call(ext, method, params or {})

            return CapabilityResult(
                capability=self.name,
                success=True,
                output=result,
            )
        except Exception as e:
            ext.error_count += 1
            ext.last_error = str(e)

            # Auto-restart on failure
            if self.config.auto_restart and ext.error_count <= self.config.max_restart_attempts:
                await self.stop_extension(extension_name)
                await asyncio.sleep(self.config.restart_delay)
                await self.start_extension(extension_name)

            return CapabilityResult(
                capability=self.name,
                success=False,
                output={"error": str(e)},
                error=str(e),
            )

    async def list_extensions(self) -> list[dict[str, Any]]:
        """
        List all discovered extensions.

        Returns:
            List of extension information dictionaries
        """
        return [
            {
                "name": ext.manifest.name,
                "version": ext.manifest.version,
                "language": ext.manifest.language.value,
                "description": ext.manifest.description,
                "status": ext.status.value,
                "methods": ext.manifest.methods,
                "call_count": ext.call_count,
                "error_count": ext.error_count,
            }
            for ext in self._extensions.values()
        ]

    async def get_extension_info(self, name: str) -> dict[str, Any] | None:
        """Get detailed information about an extension."""
        if name not in self._extensions:
            return None

        ext = self._extensions[name]
        return {
            "name": ext.manifest.name,
            "version": ext.manifest.version,
            "language": ext.manifest.language.value,
            "description": ext.manifest.description,
            "author": ext.manifest.author,
            "protocol": ext.manifest.protocol.value,
            "methods": ext.manifest.methods,
            "dependencies": ext.manifest.dependencies,
            "status": ext.status.value,
            "pid": ext.pid,
            "started_at": ext.started_at.isoformat() if ext.started_at else None,
            "call_count": ext.call_count,
            "error_count": ext.error_count,
            "last_error": ext.last_error,
            "path": str(ext.path),
        }

    async def reload_extension(self, name: str) -> bool:
        """
        Reload an extension (rebuild and restart).

        Args:
            name: Extension name

        Returns:
            True if reloaded successfully
        """
        if name not in self._extensions:
            return False

        ext = self._extensions[name]
        ext.status = ExtensionStatus.RELOADING

        await self.stop_extension(name)

        # Clear cached binary
        ext.binary_path = None

        # Rebuild and restart
        await self.start_extension(name)

        return True

    async def create_extension_template(
        self,
        name: str,
        language: ExtensionLanguage,
        methods: list[str] | None = None,
    ) -> Path:
        """
        Create a new extension from template.

        Args:
            name: Extension name
            language: Programming language
            methods: List of method names to scaffold

        Returns:
            Path to created extension directory
        """
        ext_dir = Path(self.config.extensions_dir)
        ext_path = ext_dir / name
        ext_path.mkdir(parents=True, exist_ok=True)

        methods = methods or ["hello", "process"]

        # Create manifest
        manifest = {
            "name": name,
            "version": "0.0.1",
            "language": language.value,
            "description": f"{name} extension",
            "methods": methods,
        }

        if language == ExtensionLanguage.GO:
            manifest["entry_point"] = "main.go"
            manifest["build_command"] = f"go build -o {name}"
            await self._create_go_template(ext_path, name, methods)
        elif language == ExtensionLanguage.RUST:
            manifest["entry_point"] = f"target/release/{name}"
            await self._create_rust_template(ext_path, name, methods)
        elif language in (ExtensionLanguage.JAVASCRIPT, ExtensionLanguage.TYPESCRIPT):
            ext = "ts" if language == ExtensionLanguage.TYPESCRIPT else "js"
            manifest["entry_point"] = f"index.{ext}"
            await self._create_js_template(ext_path, name, methods, language)

        (ext_path / "manifest.json").write_text(json.dumps(manifest, indent=2))

        return ext_path

    async def _create_go_template(
        self, path: Path, name: str, methods: list[str]
    ) -> None:
        """Create Go extension template."""
        # go.mod
        go_mod = f"""module {name}

go 1.21
"""
        (path / "go.mod").write_text(go_mod)

        # main.go
        method_cases = "\n".join([
            f'''        case "{m}":
            result = {m}(req.Params)'''
            for m in methods
        ])

        method_funcs = "\n\n".join([
            f'''func {m}(params map[string]interface{{}}) interface{{}} {{
    // TODO: Implement {m}
    return map[string]interface{{}}{{"message": "{m} called", "params": params}}
}}'''
            for m in methods
        ])

        main_go = f'''package main

import (
    "bufio"
    "encoding/json"
    "fmt"
    "os"
)

type Request struct {{
    Method string                 `json:"method"`
    Params map[string]interface{{}} `json:"params"`
}}

type Response struct {{
    Result interface{{}} `json:"result,omitempty"`
    Error  string      `json:"error,omitempty"`
}}

func main() {{
    scanner := bufio.NewScanner(os.Stdin)

    for scanner.Scan() {{
        line := scanner.Text()

        var req Request
        if err := json.Unmarshal([]byte(line), &req); err != nil {{
            sendError(fmt.Sprintf("Invalid request: %v", err))
            continue
        }}

        var result interface{{}}
        switch req.Method {{
{method_cases}
        default:
            sendError(fmt.Sprintf("Unknown method: %s", req.Method))
            continue
        }}

        sendResult(result)
    }}
}}

func sendResult(result interface{{}}) {{
    resp := Response{{Result: result}}
    data, _ := json.Marshal(resp)
    fmt.Println(string(data))
}}

func sendError(msg string) {{
    resp := Response{{Error: msg}}
    data, _ := json.Marshal(resp)
    fmt.Println(string(data))
}}

{method_funcs}
'''
        (path / "main.go").write_text(main_go)

    async def _create_rust_template(
        self, path: Path, name: str, methods: list[str]
    ) -> None:
        """Create Rust extension template."""
        # Cargo.toml
        cargo_toml = f'''[package]
name = "{name}"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
'''
        (path / "Cargo.toml").write_text(cargo_toml)

        # src/main.rs
        src_path = path / "src"
        src_path.mkdir(exist_ok=True)

        method_matches = "\n".join([
            f'            "{m}" => {m}(&request.params),'
            for m in methods
        ])

        method_funcs = "\n\n".join([
            f'''fn {m}(params: &serde_json::Value) -> serde_json::Value {{
    // TODO: Implement {m}
    serde_json::json!({{
        "message": "{m} called",
        "params": params
    }})
}}'''
            for m in methods
        ])

        main_rs = f'''use serde::{{Deserialize, Serialize}};
use std::io::{{self, BufRead, Write}};

#[derive(Deserialize)]
struct Request {{
    method: String,
    params: serde_json::Value,
}}

#[derive(Serialize)]
struct Response {{
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}}

fn main() {{
    let stdin = io::stdin();
    let mut stdout = io::stdout();

    for line in stdin.lock().lines() {{
        let line = match line {{
            Ok(l) => l,
            Err(_) => continue,
        }};

        let request: Request = match serde_json::from_str(&line) {{
            Ok(r) => r,
            Err(e) => {{
                send_error(&mut stdout, &format!("Invalid request: {{}}", e));
                continue;
            }}
        }};

        let result = match request.method.as_str() {{
{method_matches}
            _ => {{
                send_error(&mut stdout, &format!("Unknown method: {{}}", request.method));
                continue;
            }}
        }};

        send_result(&mut stdout, result);
    }}
}}

fn send_result(stdout: &mut io::Stdout, result: serde_json::Value) {{
    let response = Response {{
        result: Some(result),
        error: None,
    }};
    let json = serde_json::to_string(&response).unwrap();
    writeln!(stdout, "{{}}", json).unwrap();
    stdout.flush().unwrap();
}}

fn send_error(stdout: &mut io::Stdout, msg: &str) {{
    let response = Response {{
        result: None,
        error: Some(msg.to_string()),
    }};
    let json = serde_json::to_string(&response).unwrap();
    writeln!(stdout, "{{}}", json).unwrap();
    stdout.flush().unwrap();
}}

{method_funcs}
'''
        (src_path / "main.rs").write_text(main_rs)

    async def _create_js_template(
        self,
        path: Path,
        name: str,
        methods: list[str],
        language: ExtensionLanguage,
    ) -> None:
        """Create JavaScript/TypeScript extension template."""
        is_ts = language == ExtensionLanguage.TYPESCRIPT
        ext = "ts" if is_ts else "js"

        # package.json
        package_json = {
            "name": name,
            "version": "0.0.1",
            "type": "module",
            "main": f"index.{ext}",
        }
        if is_ts:
            package_json["devDependencies"] = {
                "typescript": "^5.0.0",
                "@types/node": "^20.0.0",
                "ts-node": "^10.9.0",
            }

        (path / "package.json").write_text(json.dumps(package_json, indent=2))

        # TypeScript config
        if is_ts:
            tsconfig = {
                "compilerOptions": {
                    "target": "ES2022",
                    "module": "ESNext",
                    "moduleResolution": "node",
                    "esModuleInterop": True,
                    "strict": True,
                    "outDir": "./dist",
                },
                "include": ["*.ts"],
            }
            (path / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

        # Main file
        type_defs = ""
        if is_ts:
            type_defs = """
interface Request {
    method: string;
    params: Record<string, any>;
}

interface Response {
    result?: any;
    error?: string;
}

"""

        method_cases = "\n".join([
            f"        case '{m}': result = {m}(request.params); break;"
            for m in methods
        ])

        method_funcs = "\n\n".join([
            f'''function {m}(params{': Record<string, any>' if is_ts else ''}) {{
    // TODO: Implement {m}
    return {{ message: '{m} called', params }};
}}'''
            for m in methods
        ])

        main_code = f'''import * as readline from 'readline';
{type_defs}
const rl = readline.createInterface({{
    input: process.stdin,
    output: process.stdout,
    terminal: false,
}});

rl.on('line', (line{': string' if is_ts else ''}) => {{
    try {{
        const request{': Request' if is_ts else ''} = JSON.parse(line);
        let result{': any' if is_ts else ''};

        switch (request.method) {{
{method_cases}
            default:
                sendError(`Unknown method: ${{request.method}}`);
                return;
        }}

        sendResult(result);
    }} catch (e{': any' if is_ts else ''}) {{
        sendError(`Invalid request: ${{e.message}}`);
    }}
}});

function sendResult(result{': any' if is_ts else ''}) {{
    console.log(JSON.stringify({{ result }}));
}}

function sendError(error{': string' if is_ts else ''}) {{
    console.log(JSON.stringify({{ error }}));
}}

{method_funcs}
'''
        (path / f"index.{ext}").write_text(main_code)

    async def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> CapabilityResult:
        """
        Execute a polyglot operation.

        Args:
            operation: Operation to perform
            **kwargs: Operation parameters

        Returns:
            CapabilityResult with operation output
        """
        operations = {
            "discover": self._op_discover,
            "list": self._op_list,
            "call": self._op_call,
            "start": self._op_start,
            "stop": self._op_stop,
            "reload": self._op_reload,
            "info": self._op_info,
            "create": self._op_create,
        }

        if operation not in operations:
            return CapabilityResult(
                capability=self.name,
                success=False,
                output={"error": f"Unknown operation: {operation}"},
                error=f"Supported: {list(operations.keys())}",
            )

        try:
            result = await operations[operation](**kwargs)
            return CapabilityResult(capability=self.name, success=True, output=result)
        except Exception as e:
            return CapabilityResult(
                capability=self.name,
                success=False,
                output={"error": str(e)},
                error=str(e),
            )

    async def _op_discover(self, **kwargs: Any) -> dict[str, Any]:
        """Discover extensions."""
        extensions = await self.discover()
        return {"extensions": extensions, "count": len(extensions)}

    async def _op_list(self, **kwargs: Any) -> dict[str, Any]:
        """List extensions."""
        extensions = await self.list_extensions()
        return {"extensions": extensions}

    async def _op_call(
        self,
        extension: str,
        method: str,
        params: dict | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Call extension method."""
        result = await self.call(extension, method, params)
        return result.output

    async def _op_start(self, extension: str, **kwargs: Any) -> dict[str, Any]:
        """Start extension."""
        success = await self.start_extension(extension)
        return {"success": success, "extension": extension}

    async def _op_stop(self, extension: str, **kwargs: Any) -> dict[str, Any]:
        """Stop extension."""
        success = await self.stop_extension(extension)
        return {"success": success, "extension": extension}

    async def _op_reload(self, extension: str, **kwargs: Any) -> dict[str, Any]:
        """Reload extension."""
        success = await self.reload_extension(extension)
        return {"success": success, "extension": extension}

    async def _op_info(self, extension: str, **kwargs: Any) -> dict[str, Any]:
        """Get extension info."""
        info = await self.get_extension_info(extension)
        return info or {"error": "Extension not found"}

    async def _op_create(
        self,
        name: str,
        language: str,
        methods: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create extension template."""
        lang = ExtensionLanguage(language)
        path = await self.create_extension_template(name, lang, methods)
        return {"path": str(path), "name": name, "language": language}

    async def run(self, operation: str, **kwargs: Any) -> CapabilityResult:
        """Run a polyglot operation (alias for execute)."""
        return await self.execute(operation, **kwargs)

    async def close(self) -> None:
        """Stop all extensions and cleanup."""
        for name in list(self._extensions.keys()):
            await self.stop_extension(name)

        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass

    async def __aenter__(self) -> "PolyglotCapability":
        """Async context manager entry."""
        await self._init_runners()
        await self.discover()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
