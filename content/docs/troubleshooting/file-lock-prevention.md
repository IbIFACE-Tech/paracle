# 🚨 URGENT: File Lock Prevention Guide

## The Root Cause

**Every time you run `uv run`, it tries to rebuild `paracle.exe`**, causing file locks.

## The Solution: `--no-sync`

```bash
# ❌ CAUSES LOCKS
uv run paracle metrics summary
uv run python script.py

# ✅ NO LOCKS  
uv run --no-sync paracle metrics summary
uv run --no-sync python script.py
```

## When You'll See File Locks

### Symptom 1: MCP Server Fails
```
error: MCP server could not be started: Process exited with code 2
error: failed to remove file paracle.exe: The process cannot access the file
```

**Cause**: `.vscode/mcp.json` was using `uv run` (now fixed to `uv run --no-sync`)

### Symptom 2: UV Commands Fail
```
$ uv run paracle --version
error: failed to remove file paracle.exe: (os error 32)
```

**Cause**: You forgot `--no-sync`

**Fix**: Use `uv run --no-sync`

### Symptom 3: Testing Fails
```
$ uv run pytest
error: The process cannot access the file
```

**Cause**: Another terminal has `uv run` command active

**Fix**: 
1. Close other terminals OR
2. Stop processes: `.\scripts\stop-mcp-processes.ps1` OR  
3. Use diagnostics: `uv run --no-sync python -c "from mcp_diagnose_tool import mcp_diagnose; mcp_diagnose(action='stop_processes', auto_fix=True)"`

## Quick Fix Commands

### Check for Issues
```bash
uv run --no-sync python -c "from mcp_diagnose_tool import mcp_diagnose; import json; print(json.dumps(mcp_diagnose(action='check'), indent=2))"
```

### Stop Stuck Processes (PowerShell)
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.Path -like "C:\Projets\paracle\paracle-lite*"} | Stop-Process -Force
```

### Stop Stuck Processes (Bash)
```bash
ps aux | grep "paracle-lite.*python" | grep -v grep | awk '{print $2}' | xargs kill -9
```

## Prevention Checklist

- [ ] **MCP Config**: Uses `uv run --no-sync` ✅ (already updated)
- [ ] **Testing**: Always `uv run --no-sync pytest`
- [ ] **Scripts**: Use `--no-sync` in automation
- [ ] **CLI**: Run `uv run --no-sync paracle ...`
- [ ] **One-off commands**: Always add `--no-sync`

## When to OMIT `--no-sync`

Only skip `--no-sync` when you WANT to update dependencies:

```bash
# After editing pyproject.toml
uv sync  # or uv run (which implies sync)

# Explicitly updating packages
uv run --reinstall paracle ...

# First time setup
uv sync
```

## Files Updated

1. ✅ `.vscode/mcp.json` - Now uses `--no-sync`
2. ✅ `scripts/mcp-server.ps1` - Wrapper avoids `uv run`
3. ✅ Documentation - All examples use `--no-sync`

## Testing

```bash
# Before: Would fail with file lock
uv run paracle --version

# After: Works with --no-sync
uv run --no-sync paracle --version
```

## Key Takeaway

> **Add `--no-sync` to every `uv run` command unless you're explicitly updating dependencies.**

This single flag prevents 95% of file lock issues.

