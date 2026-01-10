# MCP File Lock Resolution Scripts

## Problem

The MCP server uses `uv run` which rebuilds on every start, causing file locks on `paracle.exe`. This blocks:

- MCP server startup
- UV commands
- CLI updates

## Solutions

### 🎯 Solution 1: Use `uv run --no-sync` (Cross-Platform - Applied)

The `.vscode/mcp.json` has been updated to use `--no-sync` flag:

```json
{
  "servers": {
    "paracle": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--no-sync", "paracle", "mcp", "serve", "--stdio"]
    }
  }
}
```

**Benefits:**

- ✅ Works on Windows, Linux, macOS
- ✅ No hardcoded paths
- ✅ No rebuilds (--no-sync prevents file locks)
- ✅ Uses existing virtual environment
- ✅ No wrapper scripts needed

**Restart VS Code** to apply this change.

### 🛑 Solution 2: Stop MCP Processes Manually

If the MCP server is stuck or causing locks:

**PowerShell:**

```powershell
.\scripts\stop-mcp-processes.ps1
```

**Bash:**

```bash
./scripts/stop-mcp-processes.sh
```

### 🧹 Solution 3: Clean Reinstall

If `paracle.exe` is corrupted or locked:

**PowerShell:**

```powershell
.\scripts\clean-install-mcp.ps1
```

This will:

1. Stop all Python/Paracle processes
2. Remove `paracle.exe`
3. Reinstall with `uv sync --reinstall`

## Quick Troubleshooting

### Error: "failed to remove file paracle.exe"

1. Run stop script:

   ```powershell
   .\scripts\stop-mcp-processes.ps1
   ```

2. Restart VS Code

3. If still failing, run clean install:

   ```powershell
   .\scripts\clean-install-mcp.ps1
   ```

### MCP Server Won't Start

1. Check MCP configuration uses direct Python (not `uv run`)
2. Stop all processes
3. Restart VS Code
4. Check VS Code Output → MCP logs

### UV Commands Failing

1. Stop MCP processes first
2. Run UV command
3. Restart MCP server if needed

## Prevention

The new MCP configuration avoids rebuilds, preventing most file locks. However:

- **Always stop MCP processes** before major UV operations
- **Use the stop script** before `uv sync --reinstall`
- **Restart VS Code** after clean installs

## Alternative Configurations

### Option A: Use Installed CLI (if published)

```json
{
  "command": "paracle",
  "args": ["mcp", "serve", "--stdio"]
}
```

### Option B: Use UV with --no-sync (Current - Recommended)

Cross-platform, works everywhere:

```json
{
  "command": "uv",
  "args": ["run", "--no-sync", "paracle", "mcp", "serve", "--stdio"]
}
```

### Option C: Wrapper Scripts (Windows/Linux specific)

**Windows:**

```json
{
  "command": "pwsh",
  "args": ["-ExecutionPolicy", "Bypass", "-File", "${workspaceFolder}/scripts/mcp-server.ps1"]
}
```

**Linux/macOS:**

```json
{
  "command": "bash",
  "args": ["${workspaceFolder}/scripts/mcp-server.sh"]
}
```

## Files Created

- `scripts/stop-mcp-processes.ps1` - Stop MCP processes (PowerShell)
- `scripts/stop-mcp-processes.sh` - Stop MCP processes (Bash)
- `scripts/clean-install-mcp.ps1` - Clean reinstall (PowerShell)
- `.vscode/mcp.json` - Updated MCP configuration

## Status

✅ **MCP configuration updated** - Using `uv run --no-sync` (cross-platform)
✅ **Stop scripts created** - For manual intervention (Windows & Linux)
✅ **Wrapper scripts created** - Alternative approach if needed
✅ **Works everywhere** - Windows, Linux, macOS

**Next Step:** Restart VS Code to apply the new MCP configuration.
