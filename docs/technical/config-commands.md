# Config Commands Reference

## Overview

The `paracle config` command group provides tools for managing and inspecting Paracle's split configuration system.

## Commands

### `paracle config show`

Display the effective configuration after merging all includes.

**Usage:**
```bash
paracle config show [OPTIONS]
```

**Options:**
- `--format, -f` - Output format: `yaml` (default), `json`, or `table`
- `--section, -s` - Show specific section: `all` (default), `logs`, `adr`, or `roadmap`
- `--parac-root` - Path to .parac/ directory (default: current directory)

**Examples:**

```bash
# Show full configuration as YAML
paracle config show

# Show as JSON
paracle config show --format json

# Show as table
paracle config show --format table

# Show only logs section
paracle config show --section logs

# Show only ADR section
paracle config show --section adr

# Specify .parac/ directory
paracle config show --parac-root /path/to/project/.parac
```

**Output:**

The command shows:
1. Effective configuration after merging includes
2. List of included files with load status (✓ loaded / ✗ missing)

**Example Output (YAML):**
```yaml
logs:
  base_path: memory/logs
  global:
    max_line_length: 1000
    max_file_size_mb: 50
    async_logging: true
  predefined:
    actions:
      enabled: true
      path: agent_actions.log
    decisions:
      enabled: true
      path: decisions.log

adr:
  enabled: true
  base_path: roadmap/adr
  limits:
    max_title_length: 120
    max_total_length: 15000

roadmap:
  base_path: roadmap
  primary: roadmap.yaml
  limits:
    max_phase_name_length: 80
    max_phases: 50

Includes:
  ✓ config/logging.yaml
  ✓ config/file-management.yaml
```

---

### `paracle config validate`

Validate project configuration files for syntax and consistency.

**Usage:**
```bash
paracle config validate [OPTIONS]
```

**Options:**
- `--parac-root` - Path to .parac/ directory (default: current directory)

**Examples:**

```bash
# Validate current project configuration
paracle config validate

# Validate specific project
paracle config validate --parac-root /path/to/.parac
```

**Checks Performed:**

1. **project.yaml exists** - Required base configuration file
2. **Valid YAML syntax** - All YAML files must parse correctly
3. **Include files** - Warns if referenced files are missing
4. **Value ranges** - Warns if values are unusually large
5. **Configuration loading** - Tests that config loads without errors

**Output:**

```
✓ Configuration is valid

Warnings (1):
  • Include file not found: config/cost-tracking.yaml

Configuration loaded successfully
Includes: 2 file(s)
```

**Error Example:**
```
✗ Validation failed

Errors (1):
  • Invalid YAML syntax: expected <block end>, but found ':'
```

---

### `paracle config files`

List all configuration files and their status.

**Usage:**
```bash
paracle config files [OPTIONS]
```

**Options:**
- `--parac-root` - Path to .parac/ directory (default: current directory)

**Examples:**

```bash
# List configuration files
paracle config files

# List files in specific project
paracle config files --parac-root /path/to/.parac
```

**Output:**

```
                    Configuration Files
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ File                      ┃ Status   ┃ Size        ┃ Type    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━┩
│ project.yaml              │ ✓ Loaded │ 2,145 bytes │ Base    │
│ config/logging.yaml       │ ✓ Loaded │ 1,834 bytes │ Include │
│ config/cost-tracking.yaml │ ✗ Missing│ -           │ Include │
│ config/file-management...│ ✓ Loaded │ 8,942 bytes │ Include │
└───────────────────────────┴──────────┴─────────────┴─────────┘

Total: 4 files, 3 loaded
```

---

## Workflows

### Check Configuration After Changes

```bash
# 1. Edit configuration
nano .parac/project.yaml

# 2. Validate changes
paracle config validate

# 3. View effective configuration
paracle config show
```

### Debug Configuration Issues

```bash
# 1. Check which files are loaded
paracle config files

# 2. Validate configuration
paracle config validate

# 3. Show effective config to verify merging
paracle config show --format yaml
```

### Compare Configurations

```bash
# Show base project.yaml
cat .parac/project.yaml

# Show effective config (with includes)
paracle config show

# Show specific section
paracle config show --section logs
```

### Export Configuration

```bash
# Export as YAML
paracle config show --format yaml > config-export.yaml

# Export as JSON
paracle config show --format json > config-export.json
```

---

## Integration with Split Configuration

The `config` commands work seamlessly with the split configuration system:

**project.yaml (minimal):**
```yaml
name: my-project
version: 0.1.0

include:
  - config/logging.yaml
  - config/file-management.yaml

defaults:
  model_provider: openai
```

**Show effective config:**
```bash
paracle config show
# Shows merged configuration from all files
```

**Validate all files:**
```bash
paracle config validate
# Checks project.yaml + all includes
```

**List all files:**
```bash
paracle config files
# Shows which includes are loaded vs missing
```

---

## Troubleshooting

### "Error: .parac/ directory not found"

**Solution:**
```bash
# Run from project root
cd /path/to/your/project
paracle config show

# Or specify path
paracle config show --parac-root /path/to/project/.parac
```

### "Invalid YAML syntax"

**Solution:**
```bash
# Use validation to see detailed error
paracle config validate

# Check specific file
cat .parac/project.yaml | python -m yaml
```

### "Include file not found"

This is a **warning**, not an error. Optional include files can be missing.

**To fix:**
```bash
# Create the missing file
mkdir -p .parac/config
touch .parac/config/logging.yaml

# Or remove from includes
# Edit .parac/project.yaml and comment out the include
```

### "Failed to load configuration"

**Check:**
1. YAML syntax is valid (`paracle config validate`)
2. File permissions allow reading
3. No circular includes
4. Values are within reasonable ranges

```bash
# Debug steps
paracle config files      # Check which files exist
paracle config validate   # See detailed errors
paracle config show       # Try to load config
```

---

## Advanced Usage

### CI/CD Integration

```bash
# In CI pipeline, validate config before deployment
paracle config validate || exit 1

# Export config for deployment
paracle config show --format json > deploy-config.json
```

### Configuration Diffing

```bash
# Show current config
paracle config show > config-current.yaml

# Make changes...

# Show new config
paracle config show > config-new.yaml

# Diff
diff config-current.yaml config-new.yaml
```

### Programmatic Access

```python
from pathlib import Path
from paracle_core.parac.file_config import FileManagementConfig

# Load configuration
parac_root = Path(".parac")
config = FileManagementConfig.from_project_yaml(parac_root)

# Access values
print(config.logs.base_path)
print(config.logs.global_config.max_line_length)
print(config.adr.enabled)
```

---

## Related Documentation

- [Configuration Guide](configuration-guide.md) - Complete configuration reference
- [Split Configuration Summary](../.parac/CONFIGURATION_SPLIT_SUMMARY.md) - Split config overview
- [Testing Include Mechanism](testing-include-mechanism.md) - Technical details

---

## Command Summary

| Command           | Purpose                      | Output            |
| ----------------- | ---------------------------- | ----------------- |
| `config show`     | Display effective config     | YAML/JSON/Table   |
| `config validate` | Check configuration validity | Errors/Warnings   |
| `config files`    | List configuration files     | Table with status |

---

**Version**: 1.0
**Last Updated**: 2026-01-07
**Status**: Implemented

**Next**: Add `config diff` and `config use <profile>` commands in future versions.
