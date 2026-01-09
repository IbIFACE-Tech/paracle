# Platform-Specific Logging - Quick Reference

**TL;DR**: Paracle framework logs now go to platform-specific locations, separate from user workspace logs.

---

## Log Locations by Platform

| Platform    | Location                                         | Example                                                       |
| ----------- | ------------------------------------------------ | ------------------------------------------------------------- |
| **Windows** | `%LOCALAPPDATA%\Paracle\logs\`                   | `C:\Users\john\AppData\Local\Paracle\logs\`                   |
| **Linux**   | `~/.local/share/paracle/logs/`                   | `/home/john/.local/share/paracle/logs/`                       |
| **macOS**   | `~/Library/Application Support/Paracle/logs/`    | `/Users/john/Library/Application Support/Paracle/logs/`       |
| **Docker**  | `/var/log/paracle/logs/` or `/tmp/paracle/logs/` | `/var/log/paracle/logs/` (fallback to `/tmp` if not writable) |

---

## Log Files

| File                 | Purpose                                   |
| -------------------- | ----------------------------------------- |
| `paracle.log`        | Main framework log (all components)       |
| `paracle-cli.log`    | CLI operations and commands               |
| `paracle-agent.log`  | Agent execution framework logs            |
| `paracle-errors.log` | Framework errors only (ERROR+ level)      |
| `paracle-audit.log`  | Security audit log (ISO 42001 compliance) |

---

## User vs Framework Logs

| Type               | Location              | Purpose                                                               |
| ------------------ | --------------------- | --------------------------------------------------------------------- |
| **User Logs**      | `.parac/memory/logs/` | Project-specific actions (e.g., `agent_actions.log`, `decisions.log`) |
| **Framework Logs** | Platform-specific     | Paracle framework operations (cross-project)                          |

**Rule of Thumb**: User actions → `.parac/`, Framework operations → platform paths

---

## Quick Start

### Python API

```python
from paracle_core.logging import get_log_path, get_info, configure_logging

# Get platform info
info = get_info()
print(f"Platform: {info['platform']}")
print(f"Main log: {info['main_log']}")

# Configure logging (uses platform paths by default)
configure_logging(level="INFO", log_to_file=True)

# Get specific log paths
main_log = get_log_path("main")       # paracle.log
cli_log = get_log_path("cli")         # paracle-cli.log
errors_log = get_log_path("errors")   # paracle-errors.log
```

### CLI (Future)

```bash
# Show platform info
paracle platform info

# Tail logs
paracle logs tail                    # tail -f paracle.log
paracle logs tail --log-type cli     # tail -f paracle-cli.log

# Clean old logs
paracle logs clean --days 30
```

---

## Environment Variables

| Variable                     | Default | Description                   |
| ---------------------------- | ------- | ----------------------------- |
| `PARACLE_USE_PLATFORM_PATHS` | `true`  | Use platform-specific paths   |
| `PARACLE_LOG_FILE`           | `None`  | Override log file path        |
| `PARACLE_LOG_LEVEL`          | `INFO`  | Log level (DEBUG, INFO, etc.) |

```bash
# Disable platform paths (use explicit path)
export PARACLE_USE_PLATFORM_PATHS=false
export PARACLE_LOG_FILE=/custom/path/paracle.log

# Change log level
export PARACLE_LOG_LEVEL=DEBUG
```

---

## Platform Detection

Paracle automatically detects your platform:

```python
from paracle_core.logging.platform import detect_platform

platform = detect_platform()  # "windows", "linux", "macos", or "docker"
```

**Detection Logic:**
1. Check for Docker indicators (`/.dockerenv`, `/run/.containerenv`, `KUBERNETES_SERVICE_HOST`)
2. Check `sys.platform`:
   - `win32` → Windows
   - `darwin` → macOS
   - `linux` → Linux

---

## XDG Base Directory (Linux/Unix)

Paracle follows [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):

| XDG Variable      | Default          | Paracle Subdir  |
| ----------------- | ---------------- | --------------- |
| `XDG_DATA_HOME`   | `~/.local/share` | `paracle/logs/` |
| `XDG_CACHE_HOME`  | `~/.cache`       | `paracle/`      |
| `XDG_CONFIG_HOME` | `~/.config`      | `paracle/`      |

```bash
# Customize XDG paths
export XDG_DATA_HOME=/custom/data
export XDG_CACHE_HOME=/custom/cache
# Logs will now go to /custom/data/paracle/logs/
```

---

## Docker Best Practices

### Option 1: Mount Volume (Recommended)

```bash
docker run -v /host/logs:/var/log/paracle paracle/paracle:latest
```

Logs go to: `/var/log/paracle/logs/paracle.log` (persisted on host)

### Option 2: Use /tmp (Temporary)

If `/var/log/paracle` not writable, Paracle automatically falls back to `/tmp/paracle/logs/`

```bash
docker run paracle/paracle:latest
# Logs: /tmp/paracle/logs/paracle.log (lost on container restart)
```

### Option 3: Explicit Path

```bash
docker run -e PARACLE_LOG_FILE=/app/logs/paracle.log paracle/paracle:latest
```

---

## Troubleshooting

### Problem: Can't find logs

**Solution:**
```python
from paracle_core.logging import get_info
print(get_info())  # Shows all paths
```

### Problem: Permission denied

**Solution (Linux/macOS):**
```bash
# Ensure directory is writable
mkdir -p ~/.local/share/paracle/logs
chmod 755 ~/.local/share/paracle/logs
```

**Solution (Docker):**
```bash
# Run as root or mount volume with correct permissions
docker run -v /host/logs:/var/log/paracle:rw paracle/paracle:latest
```

### Problem: Want logs in custom location

**Solution:**
```bash
export PARACLE_USE_PLATFORM_PATHS=false
export PARACLE_LOG_FILE=/my/custom/path/paracle.log
```

---

## Testing

Test platform detection:

```bash
# Run platform tests
uv run python -m pytest tests/unit/logging/test_platform.py -v

# All 29 tests should pass:
# - Platform detection (6 tests)
# - Path generation (14 tests)
# - Log paths (5 tests)
# - Directory creation (2 tests)
# - Info generation (2 tests)
```

---

## Migration Guide

**If you have existing log files in `.parac/memory/logs/`:**

Those are **user logs** and should stay there. Examples:
- `.parac/memory/logs/agent_actions.log` ✅ (user actions)
- `.parac/memory/logs/decisions.log` ✅ (user decisions)

**New framework logs** now go to platform-specific locations:
- Framework errors, debugging, audit → platform paths

**No migration needed!** User logs and framework logs are separate.

---

## See Also

- [Phase 8 Complete Documentation](./phase_8_complete_with_platform_logging.md)
- [STRUCTURE.md](../../STRUCTURE.md) - `.parac/` structure and file placement
- [GOVERNANCE.md](../../GOVERNANCE.md) - Governance protocol

---

**Last Updated**: 2026-01-08
**Version**: 1.0
**Status**: Active
