# Log Management Guide

> **For Paracle Users** - Simple guide to managing logs in your `.parac/` workspace.

---

## 📖 Important: Two Logging Systems

Paracle has **TWO separate logging systems**:

1. **User Logs** (`.parac/memory/logs/`) - **This guide** - For your project
2. **Framework Logs** (system paths) - For Paracle framework debugging

**This guide covers User Logs only.** For the complete architecture explanation, see [Logging Architecture](logging-architecture.md).

---

## Quick Start

All log management is done through the **unified CLI**:

```bash
# Check log health
paracle logs analyze

# View recent actions
paracle logs show

# List all available logs
paracle logs list
```

## Core Commands

### 📊 Analyze - Check Log Health

```bash
paracle logs analyze
```

**What it shows:**
- Current line count and file size
- Percentage of limits used (max: 10,000 lines / 1 MB)
- Warning if approaching limit (80%+)
- Alert if rotation needed (100%+)
- Number of archived logs

**Example output:**
```
📊 Agent Actions Log Statistics
==================================================
📄 File: memory\logs\agent_actions.log
📏 Lines: 1,571
💾 Size: 0.17 MB (176.72 KB)

✅ Log size is within acceptable limits
   Lines: 1,571 / 10,000 (16%)
   Size: 0.17 / 1.0 MB (17%)

📦 Archives: None
```

### 📄 Show - View Log Contents

```bash
# Show last 50 lines (default)
paracle logs show

# Show last 100 lines
paracle logs show -n 100

# Follow log in real-time
paracle logs show -f

# Show different log
paracle logs show decisions

# Filter by pattern
paracle logs show -g "ERROR"
```

### 📋 List - Available Logs

```bash
paracle logs list
```

Shows all available log files with:
- Name (actions, decisions, runtime/*, audit/*)
- Path relative to `.parac/`
- File size
- Last modified date

### 🔄 Rotate - Archive Old Logs

```bash
# Interactive rotation (with confirmation)
paracle logs rotate

# Force rotation (no confirmation)
paracle logs rotate --force
```

**What it does:**
- Archives ALL current lines with timestamp
- Keeps last 1,000 lines for continuity
- Creates: `.parac/memory/logs/archives/agent_actions.YYYY-MM-DD_HH-MM-SS.log`

**When to use:**
- When `analyze` shows 80%+ usage
- Before major maintenance operations
- To clean up long-running projects

**Note:** Rotation is **automatic** at 10,000 lines - manual rotation is optional.

### 🧹 Cleanup - Remove Old Archives

```bash
# Preview what would be deleted (dry run)
paracle logs cleanup --dry-run

# Interactive cleanup (365 days retention)
paracle logs cleanup

# Force cleanup without confirmation
paracle logs cleanup --force

# Custom retention (e.g., 90 days)
paracle logs cleanup -d 90 -f
```

**Default retention:** 365 days (1 year)

**What it shows:**
- Number of archives older than threshold
- Total size to be freed
- List of files (in dry-run mode)
- Remaining archive count after cleanup

### 🗑️ Clear - Empty a Log

```bash
# Interactive clear (with confirmation)
paracle logs clear actions

# Force clear (no confirmation)
paracle logs clear decisions --force
```

**⚠️ Warning:** This is **destructive** and cannot be undone. Use with caution.

### 📦 Export - Export to File

```bash
# Export as JSON (default)
paracle logs export actions -o actions.json

# Export as CSV
paracle logs export actions -o actions.csv --format csv

# Export with date filter
paracle logs export actions --from-date 2026-01-01 --to-date 2026-01-31
```

## Automatic vs Manual Management

### Automatic (Built-in)
✅ **Rotation** - Triggers automatically at 10,000 lines
✅ **Logging** - All CLI commands log actions automatically
✅ **Integrity** - Archives are timestamped and organized

### Manual (When Needed)
🔄 **Rotate** - Force rotation for maintenance
🧹 **Cleanup** - Remove old archives (annually)
📊 **Analyze** - Check health periodically

## Best Practices

### 1. Monitor Regularly
```bash
# Weekly health check
paracle logs analyze
```

### 2. Clean Archives Annually
```bash
# At start of new year
paracle logs cleanup --dry-run  # Preview first
paracle logs cleanup            # Then execute
```

### 3. Rotate Before Major Work
```bash
# Before starting big feature
paracle logs rotate --force
```

### 4. Use Real-time Monitoring During Development
```bash
# In a separate terminal
paracle logs show -f
```

### 5. Export for Reports
```bash
# Monthly report
paracle logs export actions -o monthly_$(date +%Y-%m).json \
  --from-date 2026-01-01 --to-date 2026-01-31
```

## Log Files in `.parac/`

```
.parac/memory/logs/
├── agent_actions.log        # Primary log (auto-rotates)
├── decisions.log            # Important decisions
├── discoveries.log          # Learnings and insights
├── archives/                # Rotated logs
│   ├── agent_actions.2026-01-10_14-30-00.log
│   └── agent_actions.2026-01-09_09-15-30.log
├── runtime/                 # Runtime execution logs
│   └── *.log
└── audit/                   # Audit trail (ISO 42001)
    └── *.log
```

## Troubleshooting

### "No agent_actions.log found"
**Cause:** Fresh project with no logged actions yet.
**Solution:** Run any agent command - logging is automatic.

### "Log rotation needed"
**Cause:** Log has reached 10,000 lines or 1 MB.
**Solution:** Run `paracle logs rotate` or wait for auto-rotation.

### "Archives taking up space"
**Cause:** Old archives accumulating over months/years.
**Solution:** Run `paracle logs cleanup` to remove archives > 1 year old.

## Migration from Scripts

If you were using the old `.parac/tools/hooks/*.py` scripts:

**Old way (scripts):**
```bash
# ❌ Old - too complex
python .parac/tools/hooks/analyze-logs.py
python .parac/tools/hooks/rotate-logs.py
python .parac/tools/hooks/cleanup-logs.py
```

**New way (CLI):**
```bash
# ✅ New - simple and consistent
paracle logs analyze
paracle logs rotate
paracle logs cleanup
```

**Note:** The scripts still exist for backward compatibility but are **deprecated**. Use the CLI commands instead.

## API Keys & Security

**Logs do NOT contain API keys** - they are excluded by default for security.

**What IS logged:**
- ✅ Agent names and actions
- ✅ File paths and descriptions
- ✅ Timestamps and durations

**What is NOT logged:**
- ❌ API keys and secrets
- ❌ Personal data (PII)
- ❌ Credentials

## Related Documentation

- [Log Management Policy](.parac/policies/LOG_MANAGEMENT.md) - Complete policy
- [Log Rotation Policy](.parac/memory/logs/LOG_ROTATION_POLICY.md) - Technical details
- [Governance](.parac/GOVERNANCE.md) - Why logging matters

## Quick Reference Card

| Task            | Command                            |
| --------------- | ---------------------------------- |
| Check health    | `paracle logs analyze`             |
| View recent     | `paracle logs show`                |
| Follow live     | `paracle logs show -f`             |
| List all logs   | `paracle logs list`                |
| Rotate manually | `paracle logs rotate`              |
| Clean archives  | `paracle logs cleanup --dry-run`   |
| Export to file  | `paracle logs export -o file.json` |

---

**Questions?** Run `paracle logs --help` for quick reference.
