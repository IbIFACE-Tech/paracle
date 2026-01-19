# MCP Diagnostics Tool for Paracle Agents

## Overview

The `mcp_diagnose` tool allows Paracle agents to automatically detect and fix common MCP server and UV issues without human intervention.

## When to Use

Use this tool when:
- ❌ MCP server fails to start
- ❌ UV commands fail with file lock errors
- ❌ `paracle.exe` is locked on Windows
- ❌ Virtual environment is missing or corrupted
- ⚠️ Processes appear stuck or hanging

## Usage

### Check for Issues (Safe - Read Only)

```python
from paracle_tools import mcp_diagnose

# Run all diagnostic checks
result = mcp_diagnose(action="check")

print(f"Status: {result['summary']}")
# Output: {'healthy': 3, 'warnings': 1, 'errors': 0, ...}

# Check for errors
if result['summary']['has_errors']:
    print("Issues found:")
    for issue in result['issues']:
        print(f"  - {issue}")
    
    print("\nRecommended solutions:")
    for solution in result['solutions']:
        print(f"  - {solution}")
```

**Example Output:**
```json
{
  "action": "check",
  "summary": {
    "total_checks": 4,
    "healthy": 3,
    "warnings": 0,
    "errors": 1,
    "fixed": 0,
    "has_errors": true
  },
  "results": {
    "uv_available": {
      "status": "healthy",
      "issue": null,
      "details": {"uv_version": "uv 0.4.30"}
    },
    "venv_exists": {
      "status": "healthy",
      "issue": null,
      "details": {"venv_path": "C:\\...\\paracle\\.venv"}
    },
    "stuck_processes": {
      "status": "warning",
      "issue": "Found 2 potentially stuck processes",
      "solution": "Run stop-mcp-processes script"
    },
    "paracle_locked": {
      "status": "error",
      "issue": "paracle.exe is locked by another process",
      "solution": "Stop MCP processes or run: .\\scripts\\stop-mcp-processes.ps1"
    }
  },
  "issues": [
    "stuck_processes: Found 2 potentially stuck processes",
    "paracle_locked: paracle.exe is locked by another process"
  ],
  "solutions": [
    "stuck_processes: Run stop-mcp-processes script",
    "paracle_locked: Stop MCP processes or run: .\\scripts\\stop-mcp-processes.ps1"
  ],
  "next_steps": [
    "Run with action='fix' and auto_fix=True to attempt repairs"
  ]
}
```

### Auto-Fix Issues (Requires Confirmation)

```python
# Diagnose and fix all issues automatically
result = mcp_diagnose(action="fix", auto_fix=True)

if result['summary']['fixed'] > 0:
    print(f"✅ Fixed {result['summary']['fixed']} issue(s)")
    print("\nNext steps:")
    for step in result['next_steps']:
        print(f"  - {step}")
else:
    print("⚠️ Could not auto-fix issues. Manual intervention required.")
```

### Stop Stuck Processes Only

```python
# Just stop stuck MCP/Python processes
result = mcp_diagnose(action="stop_processes", auto_fix=True)

if result['results']['stop_processes']['fixed']:
    print("✅ Processes stopped successfully")
else:
    print("⚠️ Could not stop processes:", result['results']['stop_processes']['solution'])
```

### Reinstall Paracle

```python
# Clean reinstall of Paracle CLI
result = mcp_diagnose(action="reinstall", auto_fix=True)

if result['results']['reinstall']['fixed']:
    print("✅ Paracle reinstalled successfully")
    print("🔄 Restart VS Code to apply changes")
else:
    print("❌ Reinstall failed:", result['results']['reinstall']['issue'])
```

## Actions

| Action | Description | Safe? | Requires auto_fix |
|--------|-------------|-------|-------------------|
| `check` | Run all diagnostic checks | ✅ Yes (read-only) | No |
| `fix` | Diagnose and attempt to fix issues | ⚠️ Modifies system | Yes |
| `stop_processes` | Stop stuck MCP/Python processes | ⚠️ Kills processes | Yes |
| `reinstall` | Reinstall Paracle with `uv sync --reinstall` | ⚠️ Rebuilds environment | Yes |

## Diagnostic Checks

The tool performs these checks:

### 1. UV Availability
- ✅ **Healthy**: UV is installed and working
- ❌ **Error**: UV not found or failing

### 2. Virtual Environment
- ✅ **Healthy**: `.venv/` or `venv/` exists with Python
- ❌ **Error**: No virtual environment found

### 3. Stuck Processes
- ✅ **Healthy**: No stuck Python/Paracle processes
- ⚠️ **Warning**: Found processes potentially holding file locks

### 4. File Locks (Windows)
- ✅ **Healthy**: `paracle.exe` is not locked
- ❌ **Error**: File is locked by another process

## Agent Integration Examples

### CoderAgent: Before Running UV Commands

```python
# Before executing `uv sync` or similar
result = mcp_diagnose(action="check")

if result['summary']['has_errors']:
    # Try to fix automatically
    fix_result = mcp_diagnose(action="fix", auto_fix=True)
    
    if fix_result['summary']['fixed'] > 0:
        log_action("INFO", "Auto-fixed MCP/UV issues before UV command")
    else:
        log_action("ERROR", "UV issues detected but could not auto-fix")
        return {"error": "Please resolve UV issues manually", "details": result}

# Proceed with UV command
subprocess.run(["uv", "sync"], check=True)
```

### PM Agent: Monitoring System Health

```python
# Periodic health check
def check_development_environment():
    result = mcp_diagnose(action="check")
    
    health_score = (
        result['summary']['healthy'] / result['summary']['total_checks']
    ) * 100
    
    if health_score < 75:
        return {
            "status": "unhealthy",
            "score": health_score,
            "issues": result['issues'],
            "recommendation": "Run diagnostics with auto_fix=True"
        }
    
    return {"status": "healthy", "score": health_score}
```

### Reviewer Agent: Pre-Commit Validation

```python
# Before allowing commits
def validate_environment_before_commit():
    result = mcp_diagnose(action="check")
    
    # Block commit if critical errors
    if any("error" in str(r).lower() for r in result['results'].values()):
        return {
            "allow_commit": False,
            "reason": "MCP/UV environment has errors",
            "fixes_required": result['solutions']
        }
    
    return {"allow_commit": True}
```

## Security Considerations

- 🔒 **Process Stopping**: Only stops processes within project directory
- 🔒 **File Access**: Only checks/modifies project files
- 🔒 **Command Execution**: Uses subprocess with timeout limits
- ⚠️ **auto_fix=True**: Use with caution - kills processes and modifies files

## Troubleshooting

### Issue: "MCP server could not be started: Process exited with code 2"

```python
result = mcp_diagnose(action="fix", auto_fix=True)
# This will stop processes and reinstall if needed
```

### Issue: "failed to remove file paracle.exe: The process cannot access the file"

```python
result = mcp_diagnose(action="stop_processes", auto_fix=True)
# Then restart VS Code
```

### Issue: Virtual environment missing

```python
result = mcp_diagnose(action="fix", auto_fix=True)
# Will run `uv sync` to create venv
```

## API Reference

### mcp_diagnose()

```python
def mcp_diagnose(
    action: Literal["check", "fix", "stop_processes", "reinstall"] = "check",
    auto_fix: bool = False,
) -> dict[str, dict]:
    """
    Diagnose and fix MCP server and UV issues.
    
    Args:
        action: Action to perform ("check", "fix", "stop_processes", "reinstall")
        auto_fix: If True, automatically apply fixes (default: False)
    
    Returns:
        Dictionary with:
        - action: Action performed
        - summary: Overview (healthy, warnings, errors, fixed counts)
        - results: Detailed results per check
        - issues: List of problems found
        - solutions: Recommended solutions
        - next_steps: What to do next
    """
```

## Related Files

- **Tool Implementation**: `packages/paracle_tools/mcp_diagnose_tool.py`
- **Diagnostics Engine**: `packages/paracle_tools/mcp_diagnostics.py`
- **PowerShell Scripts**: `scripts/stop-mcp-processes.ps1`, `scripts/clean-install-mcp.ps1`
- **Bash Scripts**: `scripts/stop-mcp-processes.sh`, `scripts/mcp-server.sh`
- **MCP Configuration**: `.vscode/mcp.json`

## Version

- **Added**: v1.0.3
- **Status**: Production ready
- **Platform**: Windows, Linux, macOS

