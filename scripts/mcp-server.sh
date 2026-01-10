#!/bin/bash
# MCP Server Wrapper - Production Ready (Bash)
# Automatically detects virtual environment and runs MCP server

set -e

# Find project root (where pyproject.toml is)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Detect virtual environment
PYTHON_EXE=""
for path in \
    "$PROJECT_ROOT/.venv/bin/python" \
    "$PROJECT_ROOT/venv/bin/python" \
    "$PROJECT_ROOT/.venv/Scripts/python.exe" \
    "$PROJECT_ROOT/venv/Scripts/python.exe"; do
    if [ -f "$path" ]; then
        PYTHON_EXE="$path"
        break
    fi
done

if [ -z "$PYTHON_EXE" ]; then
    # Fallback to system Python with uv run
    exec uv run paracle mcp serve --stdio
fi

# Set PYTHONPATH to include packages
export PYTHONPATH="$PROJECT_ROOT/packages"

# Run MCP server directly (no rebuild)
exec "$PYTHON_EXE" -m paracle_mcp.server --stdio
