# 🔧 mcp_diagnose Quick Reference for Agents

## When to Use

Use `mcp_diagnose` when you encounter:
- ❌ "MCP server could not be started: Process exited with code 2"
- ❌ "failed to remove file paracle.exe: The process cannot access the file"
- ❌ UV commands failing with file lock errors
- ⚠️ Processes appear stuck or hanging

## Quick Commands

```python
from paracle_tools import mcp_diagnose

# 1. CHECK (Safe - read only)
result = mcp_diagnose(action="check")

# 2. FIX ALL (Attempts auto-fix)
result = mcp_diagnose(action="fix", auto_fix=True)

# 3. STOP PROCESSES (Just kill stuck processes)
result = mcp_diagnose(action="stop_processes", auto_fix=True)

# 4. REINSTALL (Clean rebuild)
result = mcp_diagnose(action="reinstall", auto_fix=True)
```

## Common Patterns

### Before UV Commands
```python
# Check environment health before UV operations
result = mcp_diagnose(action="check")
if result['summary']['has_errors']:
    mcp_diagnose(action="fix", auto_fix=True)
subprocess.run(["uv", "sync"], check=True)
```

### Error Recovery
```python
try:
    subprocess.run(["uv", "run", "paracle", "..."], check=True)
except subprocess.CalledProcessError:
    # Try to fix and retry
    result = mcp_diagnose(action="fix", auto_fix=True)
    if result['summary']['fixed'] > 0:
        subprocess.run(["uv", "run", "paracle", "..."], check=True)
```

### Health Check
```python
result = mcp_diagnose(action="check")
health_score = (result['summary']['healthy'] / result['summary']['total_checks']) * 100
print(f"Environment health: {health_score}%")
```

## Output Format

```json
{
  "action": "check",
  "summary": {
    "healthy": 3,      // ✅ Passed
    "warnings": 1,     // ⚠️  Potential issues
    "errors": 0,       // ❌ Critical problems
    "fixed": 0,        // 🔧 Auto-fixed (if auto_fix=True)
    "has_errors": false
  },
  "results": { ... },  // Detailed per-check results
  "issues": [ ... ],   // List of problems found
  "solutions": [ ... ], // Recommended fixes
  "next_steps": [ ... ] // What to do next
}
```

## Safety

- ✅ `action="check"` is **always safe** (read-only)
- ⚠️ `auto_fix=True` will:
  - Kill processes in project directory
  - Run `uv sync --reinstall`
  - Modify system state

## Documentation

- **Full Guide**: `content/docs/tools/mcp-diagnostics-tool.md`
- **Implementation**: `MCP-DIAGNOSTICS-IMPLEMENTATION.md`
- **Manual Fixes**: `scripts/README-MCP-FIX.md`

