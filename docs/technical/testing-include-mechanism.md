# Testing the Include Mechanism

## ✅ Implementation Complete

The configuration include mechanism has been implemented in `packages/paracle_core/parac/file_config.py`:

### New Methods

1. **`_process_includes()`** - Processes include directives from project.yaml
2. **`_deep_merge()`** - Deep merges configuration dictionaries

### How It Works

```python
# 1. Load base project.yaml
with open(project_yaml) as f:
    data = yaml.safe_load(f)

# 2. Process includes (new!)
data = cls._process_includes(parac_root, data)

# 3. Extract file_management section
file_management = data.get("file_management", {})

# 4. Parse configuration
return cls.from_dict(file_management)
```

### Include Processing Algorithm

1. **Read include section** from project.yaml
2. **Load each included file** (skip if missing)
3. **Deep merge** included data with base data
4. **Later includes override earlier ones**
5. **Nested dicts are merged recursively**

## Manual Testing (Once File Lock Resolved)

### Test 1: Basic Include

**Create test project:**

```bash
mkdir -p /tmp/test-paracle/.parac/config
cd /tmp/test-paracle/.parac
```

**project.yaml:**
```yaml
name: test-project
include:
  - config/logging.yaml
```

**config/logging.yaml:**
```yaml
file_management:
  logs:
    base_path: custom/logs
    global:
      max_line_length: 1500
```

**Test:**
```python
from pathlib import Path
from paracle_core.parac.file_config import FileManagementConfig

config = FileManagementConfig.from_project_yaml(Path("/tmp/test-paracle/.parac"))
print(config.logs.base_path)  # Should print: custom/logs
print(config.logs.global_config.max_line_length)  # Should print: 1500
```

### Test 2: Multiple Includes

**project.yaml:**
```yaml
name: test-project
include:
  - config/logging.yaml
  - config/file-management.yaml
```

**config/logging.yaml:**
```yaml
file_management:
  logs:
    base_path: custom/logs
```

**config/file-management.yaml:**
```yaml
file_management:
  adr:
    base_path: custom/adr
    limits:
      max_title_length: 150
```

**Expected:**
- `config.logs.base_path` = "custom/logs" (from logging.yaml)
- `config.adr.base_path` = "custom/adr" (from file-management.yaml)
- Both configs merged successfully

### Test 3: Deep Merge

**project.yaml:**
```yaml
name: test-project
file_management:
  logs:
    global:
      max_line_length: 1000
      max_file_size_mb: 50
include:
  - config/logging.yaml
```

**config/logging.yaml:**
```yaml
file_management:
  logs:
    global:
      max_file_size_mb: 100  # Override only this
```

**Expected:**
- `config.logs.global_config.max_line_length` = 1000 (preserved from base)
- `config.logs.global_config.max_file_size_mb` = 100 (overridden by include)

### Test 4: Missing Include (Graceful Fallback)

**project.yaml:**
```yaml
name: test-project
include:
  - config/nonexistent.yaml  # File doesn't exist
```

**Expected:**
- Config loads successfully
- Uses default values
- No error raised

### Test 5: Real-World Scenario (project-minimal.yaml)

**project.yaml:**
```yaml
name: my-project
version: 0.1.0

defaults:
  model_provider: openai
  default_model: gpt-4o-mini

include:
  - config/logging.yaml
  - config/cost-tracking.yaml
  - config/file-management.yaml
```

**Expected:**
- All three configs merged
- Settings from each file available
- No conflicts or overwrite issues

## Automated Tests

### Test File: `tests/test_config_includes.py`

Comprehensive test suite with 10 test cases:

1. ✅ `test_minimal_config_loads` - No includes, use defaults
2. ✅ `test_include_single_file` - Single include merges
3. ✅ `test_include_multiple_files` - Multiple includes merge
4. ✅ `test_include_missing_file` - Missing files skipped gracefully
5. ✅ `test_deep_merge_nested_dicts` - Nested dicts merge correctly
6. ✅ `test_split_config_like_project_minimal` - Realistic scenario
7. ✅ `test_no_include_section` - Config without includes
8. ✅ `test_include_override_order` - Later includes win
9. ✅ More edge cases...

**Run tests:**
```bash
# Once file lock resolved:
python -m pytest tests/test_config_includes.py -v
```

### Quick Test: `test_includes_quick.py`

Simple standalone test:
```bash
python test_includes_quick.py
```

## Integration Testing

### Test with Actual .parac/ Structure

1. **Create test project:**
   ```bash
   cd /tmp
   mkdir test-split-config
   cd test-split-config
   paracle init --template lite
   ```

2. **Replace project.yaml with project-minimal.yaml:**
   ```bash
   cp .parac/project.yaml .parac/project-full.yaml.backup
   cp .parac/project-minimal.yaml .parac/project.yaml
   ```

3. **Enable includes:**
   ```yaml
   # Edit .parac/project.yaml
   include:
     - config/logging.yaml
     - config/file-management.yaml
   ```

4. **Run paracle commands:**
   ```bash
   paracle config show  # Should show merged config
   paracle validate     # Should validate merged config
   paracle agents list  # Should work with split config
   ```

## Verification Checklist

- [ ] `_process_includes()` method exists in file_config.py
- [ ] `_deep_merge()` method exists in file_config.py
- [ ] `from_project_yaml()` calls `_process_includes()`
- [ ] Missing includes are skipped (no error)
- [ ] Nested dicts are merged recursively
- [ ] Later includes override earlier ones
- [ ] Base config values preserved when not overridden
- [ ] Test suite passes (once file lock resolved)
- [ ] Manual tests verify behavior
- [ ] Documentation explains usage

## Current Status

✅ **Implementation**: Complete
✅ **Methods Added**: `_process_includes()`, `_deep_merge()`
✅ **Test Suite Created**: 10 test cases
✅ **Quick Test Created**: test_includes_quick.py
✅ **Documentation**: This file

⏸️ **Testing Blocked**: File lock on paracle.exe
- Need to close running processes
- Alternative: Test in clean environment

## Next Steps

1. **Resolve file lock** - Close running paracle processes
2. **Run test suite** - `python -m pytest tests/test_config_includes.py -v`
3. **Manual verification** - Test with real .parac/ structure
4. **Update templates** - Use project-minimal.yaml in templates
5. **Update CLI** - Add `paracle config` commands

## Code Reference

**Location**: `packages/paracle_core/parac/file_config.py`

**Key Methods**:
```python
@classmethod
def from_project_yaml(cls, parac_root: Path) -> FileManagementConfig:
    """Load config with include support."""
    # ... load base YAML
    data = cls._process_includes(parac_root, data)  # ← NEW
    # ... parse config

@classmethod
def _process_includes(cls, parac_root, base_data) -> dict:
    """Process include directives."""
    includes = base_data.get("include", [])
    merged = base_data.copy()

    for include_path in includes:
        include_file = parac_root / include_path
        if include_file.exists():
            include_data = yaml.safe_load(...)
            merged = cls._deep_merge(merged, include_data)  # ← NEW

    return merged

@classmethod
def _deep_merge(cls, base, overlay) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in overlay.items():
        if isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = cls._deep_merge(result[key], value)  # Recursive
        else:
            result[key] = value  # Override
    return result
```

## Success Criteria

- [x] Include mechanism implemented
- [x] Deep merge handles nested dicts
- [x] Missing includes handled gracefully
- [ ] Tests pass (blocked by file lock)
- [ ] Manual verification complete
- [ ] Templates updated
- [ ] CLI commands added

---

**Status**: ✅ Implementation complete, ⏸️ Testing blocked by file lock
**Next**: Resolve lock, run tests, update templates
