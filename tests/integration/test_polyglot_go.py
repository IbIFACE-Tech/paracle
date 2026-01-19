"""
Integration tests for PolyglotCapability with Go extensions.

Tests the full flow:
1. Create Go extension template
2. Build the extension
3. Start the extension process
4. Call methods
5. Stop the extension
"""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from paracle_meta.capabilities.polyglot import (
    ExtensionLanguage,
    GoRunner,
    PolyglotCapability,
    PolyglotConfig,
)


@pytest.fixture
def temp_extensions_dir():
    """Create a temporary directory for extensions."""
    temp_dir = tempfile.mkdtemp(prefix="paracle_test_extensions_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def polyglot_config(temp_extensions_dir):
    """Create a test configuration."""
    return PolyglotConfig(
        extensions_dir=temp_extensions_dir,
        cache_dir=tempfile.mkdtemp(prefix="paracle_test_cache_"),
        auto_build=True,
        request_timeout=30,
    )


class TestGoRunner:
    """Test Go runner functionality."""

    @pytest.mark.asyncio
    async def test_go_is_available(self, polyglot_config):
        """Test that Go runtime is detected."""
        runner = GoRunner(polyglot_config)
        available = await runner.is_available()

        # This test will pass if Go is installed
        if available:
            print("Go is available on this system")
        else:
            pytest.skip("Go is not installed on this system")


class TestPolyglotCapability:
    """Test PolyglotCapability with Go extensions."""

    @pytest.mark.asyncio
    async def test_create_go_extension_template(self, polyglot_config):
        """Test creating a Go extension template."""
        polyglot = PolyglotCapability(config=polyglot_config)

        # Create extension template
        path = await polyglot.create_extension_template(
            name="test-calculator",
            language=ExtensionLanguage.GO,
            methods=["add", "multiply"],
        )

        assert path.exists()
        assert (path / "manifest.json").exists()
        assert (path / "main.go").exists()
        assert (path / "go.mod").exists()

        # Check manifest content
        manifest = json.loads((path / "manifest.json").read_text())
        assert manifest["name"] == "test-calculator"
        assert manifest["language"] == "go"
        assert "add" in manifest["methods"]
        assert "multiply" in manifest["methods"]

        # Check Go code contains method stubs
        go_code = (path / "main.go").read_text()
        assert "func add(" in go_code
        assert "func multiply(" in go_code
        assert 'case "add":' in go_code
        assert 'case "multiply":' in go_code

    @pytest.mark.asyncio
    async def test_discover_extensions(self, polyglot_config):
        """Test discovering extensions in directory."""
        polyglot = PolyglotCapability(config=polyglot_config)

        # Create an extension first
        await polyglot.create_extension_template(
            name="discoverable-ext", language=ExtensionLanguage.GO, methods=["test"]
        )

        # Discover
        extensions = await polyglot.discover()

        assert "discoverable-ext" in extensions

        # List should also work
        ext_list = await polyglot.list_extensions()
        names = [e["name"] for e in ext_list]
        assert "discoverable-ext" in names

    @pytest.mark.asyncio
    async def test_build_go_extension(self, polyglot_config):
        """Test building a Go extension."""
        polyglot = PolyglotCapability(config=polyglot_config)

        # Create extension
        path = await polyglot.create_extension_template(
            name="buildable-ext", language=ExtensionLanguage.GO, methods=["hello"]
        )

        # Discover to register
        await polyglot.discover()

        # Get runner and build
        runner = GoRunner(polyglot_config)
        if not await runner.is_available():
            pytest.skip("Go is not installed")

        ext_info = polyglot._extensions["buildable-ext"]
        binary_path = await runner.build(ext_info)

        assert binary_path.exists()
        print(f"Built binary at: {binary_path}")

    @pytest.mark.asyncio
    async def test_full_go_extension_flow(self, polyglot_config):
        """Test the complete flow: create, build, start, call, stop."""
        polyglot = PolyglotCapability(config=polyglot_config)

        # Check Go availability first
        runner = GoRunner(polyglot_config)
        if not await runner.is_available():
            pytest.skip("Go is not installed")

        # 1. Create extension with custom implementation
        ext_path = Path(polyglot_config.extensions_dir) / "math-ext"
        ext_path.mkdir(parents=True, exist_ok=True)

        # Custom Go code that actually does math
        go_code = """package main

import (
    "bufio"
    "encoding/json"
    "fmt"
    "os"
)

type Request struct {
    Method string                 `json:"method"`
    Params map[string]interface{} `json:"params"`
}

type Response struct {
    Result interface{} `json:"result,omitempty"`
    Error  string      `json:"error,omitempty"`
}

func main() {
    scanner := bufio.NewScanner(os.Stdin)

    for scanner.Scan() {
        line := scanner.Text()

        var req Request
        if err := json.Unmarshal([]byte(line), &req); err != nil {
            sendError(fmt.Sprintf("Invalid request: %v", err))
            continue
        }

        var result interface{}
        switch req.Method {
        case "add":
            a := req.Params["a"].(float64)
            b := req.Params["b"].(float64)
            result = map[string]interface{}{"sum": a + b}
        case "multiply":
            a := req.Params["a"].(float64)
            b := req.Params["b"].(float64)
            result = map[string]interface{}{"product": a * b}
        case "echo":
            result = map[string]interface{}{"echo": req.Params}
        default:
            sendError(fmt.Sprintf("Unknown method: %s", req.Method))
            continue
        }

        sendResult(result)
    }
}

func sendResult(result interface{}) {
    resp := Response{Result: result}
    data, _ := json.Marshal(resp)
    fmt.Println(string(data))
}

func sendError(msg string) {
    resp := Response{Error: msg}
    data, _ := json.Marshal(resp)
    fmt.Println(string(data))
}
"""
        (ext_path / "main.go").write_text(go_code)

        go_mod = """module math-ext

go 1.21
"""
        (ext_path / "go.mod").write_text(go_mod)

        manifest = {
            "name": "math-ext",
            "version": "1.0.0",
            "language": "go",
            "description": "Math operations extension",
            "methods": ["add", "multiply", "echo"],
            "entry_point": "main.go",
        }
        (ext_path / "manifest.json").write_text(json.dumps(manifest, indent=2))

        # 2. Discover
        extensions = await polyglot.discover()
        assert "math-ext" in extensions

        # 3. Call add method (auto-starts)
        result = await polyglot.call("math-ext", "add", {"a": 5, "b": 3})

        assert result.success, f"Call failed: {result.error}"
        assert "result" in result.output
        assert result.output["result"]["sum"] == 8.0

        # 4. Call multiply method
        result = await polyglot.call("math-ext", "multiply", {"a": 4, "b": 7})

        assert result.success
        assert result.output["result"]["product"] == 28.0

        # 5. Call echo method
        result = await polyglot.call(
            "math-ext", "echo", {"message": "hello", "count": 42}
        )

        assert result.success
        assert result.output["result"]["echo"]["message"] == "hello"
        assert result.output["result"]["echo"]["count"] == 42

        # 6. Check extension info
        info = await polyglot.get_extension_info("math-ext")
        assert info is not None
        assert info["status"] == "running"
        assert info["call_count"] == 3

        # 7. Stop extension
        stopped = await polyglot.stop_extension("math-ext")
        assert stopped

        info = await polyglot.get_extension_info("math-ext")
        assert info["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_extension_error_handling(self, polyglot_config):
        """Test error handling for unknown methods."""
        polyglot = PolyglotCapability(config=polyglot_config)

        runner = GoRunner(polyglot_config)
        if not await runner.is_available():
            pytest.skip("Go is not installed")

        # Create simple extension
        await polyglot.create_extension_template(
            name="error-test", language=ExtensionLanguage.GO, methods=["valid_method"]
        )

        await polyglot.discover()

        # Call valid method first to start
        result = await polyglot.call("error-test", "valid_method", {})
        assert result.success

        # Call unknown method
        result = await polyglot.call("error-test", "unknown_method", {})

        # The extension should return an error in the response
        assert "error" in result.output or not result.success

        await polyglot.stop_extension("error-test")

    @pytest.mark.asyncio
    async def test_extension_not_found(self, polyglot_config):
        """Test calling non-existent extension."""
        polyglot = PolyglotCapability(config=polyglot_config)

        result = await polyglot.call("non-existent", "method", {})

        assert not result.success
        assert "not found" in result.error.lower()


class TestPolyglotExecuteInterface:
    """Test the execute() interface."""

    @pytest.mark.asyncio
    async def test_execute_discover(self, polyglot_config):
        """Test execute with discover operation."""
        polyglot = PolyglotCapability(config=polyglot_config)

        result = await polyglot.execute("discover")

        assert result.success
        assert "extensions" in result.output
        assert "count" in result.output

    @pytest.mark.asyncio
    async def test_execute_create(self, polyglot_config):
        """Test execute with create operation."""
        polyglot = PolyglotCapability(config=polyglot_config)

        result = await polyglot.execute(
            "create", name="exec-test", language="go", methods=["test"]
        )

        assert result.success
        assert "path" in result.output
        assert Path(result.output["path"]).exists()

    @pytest.mark.asyncio
    async def test_execute_unknown_operation(self, polyglot_config):
        """Test execute with unknown operation."""
        polyglot = PolyglotCapability(config=polyglot_config)

        result = await polyglot.execute("unknown_op")

        assert not result.success
        assert "error" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
