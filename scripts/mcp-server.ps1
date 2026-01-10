#!/usr/bin/env pwsh
# MCP Server Wrapper - Production Ready
# Automatically detects virtual environment and runs MCP server

$ErrorActionPreference = "Stop"

# Find project root (where pyproject.toml is)
$scriptDir = Split-Path -Parent $PSCommandPath
$projectRoot = Split-Path -Parent $scriptDir

# Detect virtual environment
$venvPaths = @(
    "$projectRoot\.venv\Scripts\python.exe",           # Windows UV/venv
    "$projectRoot\venv\Scripts\python.exe",            # Windows standard venv
    "$projectRoot\.venv\bin\python",                   # Unix UV/venv
    "$projectRoot\venv\bin\python"                     # Unix standard venv
)

$pythonExe = $null
foreach ($path in $venvPaths) {
    if (Test-Path $path) {
        $pythonExe = $path
        break
    }
}

if (-not $pythonExe) {
    # Fallback to system Python with uv run
    & uv run paracle mcp serve --stdio
    exit $LASTEXITCODE
}

# Set PYTHONPATH to include packages
$env:PYTHONPATH = "$projectRoot\packages"

# Run MCP server directly (no rebuild)
& $pythonExe -m paracle_mcp.server --stdio
exit $LASTEXITCODE
