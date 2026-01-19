# Roadmap-State Synchronization Guide

**Last Updated**: 2026-01-17
**Version**: 1.0
**Target Audience**: Project Managers, Technical Leads

---

## Overview

This guide explains the `paracle sync --roadmap` command, which ensures alignment between:

- **`.parac/roadmap/roadmap.yaml`** - Strategic roadmap (planned phases, deliverables, metrics)
- **`.parac/memory/context/current_state.yaml`** - Operational state (actual progress, completed items)

**Why it matters**: Misalignment causes confusion, incorrect status reports, and bad decisions.

---

## The Problem

In long-running projects, **roadmap drift** occurs:

```yaml
# roadmap.yaml says:
phases:
  - id: phase_10
    status: in_progress
    deliverables:
      - name: "Feature X"
        status: completed # ← Marked done

# But current_state.yaml says:
current_phase:
  id: phase_10
  completed: [] # ← Not listed!
```

**Result**: Dashboards show incorrect progress, team members confused about status.

---

## Solution: `paracle sync --roadmap`

### What It Does

1. **Reads both files** - roadmap.yaml and current_state.yaml
2. **Detects discrepancies**:
   - Phase name/status mismatches
   - Completion % differences
   - Missing/extra deliverables
   - Metric inconsistencies
3. **Generates report** - Lists all misalignments with severity
4. **Suggests fixes** - Provides exact YAML changes needed

---

## Usage

### Basic Sync Check

```bash
# Check alignment (read-only)
paracle sync --roadmap
```

**Output**:

```
🔍 Roadmap-State Synchronization Check
======================================

✅ Phase alignment: OK
   - Roadmap: phase_10 (in_progress)
   - State:   phase_10 (in_progress)

⚠️  Progress mismatch detected:
   - Roadmap: 95%
   - State:   90%
   → Update current_state.yaml progress to 95%

❌ Deliverable mismatch:
   - Roadmap shows "Feature X" as completed
   - State does not list "Feature X" in completed
   → Add "feature_x" to current_state.yaml completed list

📊 Summary:
   - 1 phase aligned
   - 1 progress mismatch (WARNING)
   - 1 deliverable mismatch (ERROR)

🎯 Action Required: Fix 2 issues
```

---

### Auto-Fix Mode (Experimental)

```bash
# Fix discrepancies automatically
paracle sync --roadmap --fix
```

**⚠️ WARNING**: Backup files before using `--fix`. Always review changes.

---

## Validation Rules

### Rule 1: Phase Alignment

**Check**: Current phase in both files must match.

```yaml
# ✅ VALID
# roadmap.yaml
phases:
  - id: phase_10
    status: in_progress

# current_state.yaml
current_phase:
  id: phase_10
  status: in_progress
```

```yaml
# ❌ INVALID
# roadmap.yaml
phases:
  - id: phase_10 # ← Says phase_10

# current_state.yaml
current_phase:
  id: phase_9 # ← Says phase_9
```

**Fix**: Update current_state.yaml to match roadmap.yaml (roadmap is source of truth for phase transitions).

---

### Rule 2: Progress Percentage

**Check**: Progress % should be consistent within ±5%.

```yaml
# ✅ VALID (within tolerance)
# roadmap.yaml
phases:
  - id: phase_10
    progress: 95%

# current_state.yaml
current_phase:
  progress: 95%
```

```yaml
# ⚠️  WARNING (10% difference)
# roadmap.yaml
phases:
  - id: phase_10
    progress: 95%

# current_state.yaml
current_phase:
  progress: 85% # ← 10% behind
```

**Fix**: Update current_state.yaml progress if roadmap is accurate. Update roadmap if estimate changed.

---

### Rule 3: Deliverable Status

**Check**: Completed deliverables in roadmap must exist in current_state completed list.

```yaml
# ✅ VALID
# roadmap.yaml
deliverables:
  - name: "Feature X"
    status: completed

# current_state.yaml
current_phase:
  completed:
    - feature_x # ← Matches
```

```yaml
# ❌ INVALID
# roadmap.yaml
deliverables:
  - name: "Feature X"
    status: completed # ← Says completed

# current_state.yaml
current_phase:
  completed: [] # ← Not listed!
```

**Fix**: Add deliverable to current_state.yaml completed list (if truly done) or change roadmap status to `in_progress`.

---

### Rule 4: Metric Consistency

**Check**: Metrics in both files should match.

```yaml
# ✅ VALID
# roadmap.yaml
metrics:
  test_coverage: 85

# current_state.yaml
metrics:
  coverage: 85%
```

```yaml
# ⚠️  WARNING
# roadmap.yaml
metrics:
  test_coverage: 85

# current_state.yaml
metrics:
  coverage: 75%    # ← 10% lower
```

**Fix**: Update metrics to reflect actual measurements (run `make test-coverage` to get real value).

---

## Common Scenarios

### Scenario 1: Deliverable Just Completed

**Problem**: You completed a deliverable but didn't update current_state.yaml.

**Steps**:

1. Mark deliverable as completed in roadmap.yaml
2. Run `paracle sync --roadmap` (detects mismatch)
3. Update current_state.yaml:

```yaml
# Add to current_state.yaml
current_phase:
  completed:
    - feature_x # ← Add this
  progress: 95% # ← Update percentage
```

4. Re-run `paracle sync --roadmap` (should show ✅ aligned)

---

### Scenario 2: Phase Transition

**Problem**: Moving from phase_10 to phase_11, files out of sync.

**Steps**:

1. Update roadmap.yaml:

```yaml
phases:
  - id: phase_10
    status: completed
    completed_date: "2026-01-17"
  - id: phase_11
    status: in_progress
    started_date: "2026-01-17"
```

2. Update current_state.yaml:

```yaml
current_phase:
  id: phase_11
  status: in_progress
  progress: 0%
  completed: []

previous_phase:
  id: phase_10
  status: completed
  progress: 100%
```

3. Run `paracle sync --roadmap` (should confirm alignment)

---

### Scenario 3: Roadmap Estimate Changed

**Problem**: Realized deliverable is more complex, roadmap estimate wrong.

**Steps**:

1. Update roadmap.yaml metrics/progress
2. Run `paracle sync --roadmap` (shows mismatch)
3. Update current_state.yaml to match new reality
4. Document reason in `.parac/roadmap/decisions.md`:

```markdown
## ADR-XXX: Revised Phase 10 Timeline

**Context**: Feature X more complex than estimated.

**Decision**: Extended timeline by 2 weeks.

**Consequences**: Phase 10 completion pushed to 2026-02-01.
```

---

## Integration with Git Workflows

### Pre-Commit Hook

Add validation to `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Check roadmap-state alignment before commit
if git diff --cached --name-only | grep -E '(roadmap\.yaml|current_state\.yaml)'; then
    echo "🔍 Validating roadmap-state alignment..."
    paracle sync --roadmap

    if [ $? -ne 0 ]; then
        echo "❌ Roadmap-state misalignment detected!"
        echo "👉 Fix issues or use 'git commit --no-verify' to bypass"
        exit 1
    fi

    echo "✅ Roadmap-state aligned"
fi
```

---

### CI/CD Validation

Add to `.github/workflows/validate.yml`:

```yaml
name: Validate Governance
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install Paracle
        run: pip install -e .

      - name: Validate Roadmap-State Sync
        run: paracle sync --roadmap
```

---

## Troubleshooting

### Error: `roadmap.yaml not found`

**Solution**: Initialize roadmap first.

```bash
paracle init roadmap
```

---

### Error: `current_state.yaml not found`

**Solution**: Initialize project state.

```bash
paracle init state
```

---

### Warning: `Progress % mismatch (tolerance exceeded)`

**Diagnosis**:

- Roadmap: 95%
- State: 80%
- Difference: 15% (tolerance: 5%)

**Solution**:

1. Verify actual progress (count completed deliverables)
2. Update the **incorrect** file
3. Re-run validation

---

### Error: `Deliverable 'feature_x' marked completed but not in state`

**Solution**: Add to current_state.yaml:

```yaml
current_phase:
  completed:
    - feature_x # ← Add this line
```

---

## Best Practices

### ✅ DO

- ✅ Run `paracle sync --roadmap` **before** every milestone review
- ✅ Run validation **after** updating either file
- ✅ Automate validation in CI/CD
- ✅ Document reasons for misalignments in decisions.md
- ✅ Use pre-commit hooks to catch issues early

### ❌ DON'T

- ❌ Don't manually edit files without validating
- ❌ Don't ignore validation warnings (fix or document why)
- ❌ Don't update one file without updating the other
- ❌ Don't bypass validation in CI/CD
- ❌ Don't use `--fix` without reviewing changes first

---

## Workflow Recommendation

### Daily Workflow

```bash
# Start of day
paracle sync --roadmap    # Check alignment

# Work on deliverables...

# End of day (if milestone reached)
# 1. Update current_state.yaml
nano .parac/memory/context/current_state.yaml

# 2. Validate alignment
paracle sync --roadmap

# 3. Commit if aligned
git add .parac/
git commit -m "chore: update progress - feature X completed"
```

---

### Weekly Review

```bash
# Generate status report
paracle status --report

# Validate governance
paracle validate

# Check roadmap alignment
paracle sync --roadmap

# If issues found, fix before proceeding
```

---

## Advanced: Custom Validation Rules

### Add Project-Specific Rules

Edit `.parac/config/sync_rules.yaml`:

```yaml
sync_rules:
  phase_alignment:
    enabled: true
    severity: error

  progress_tolerance:
    enabled: true
    tolerance: 5 # Allow ±5% difference
    severity: warning

  deliverable_tracking:
    enabled: true
    require_dates: true # Require completion dates
    severity: error

  metric_tracking:
    enabled: true
    required_metrics:
      - test_coverage
      - security_score
    tolerance: 3 # Allow ±3 units
    severity: warning
```

---

## Support

- **Documentation**: https://docs.paracles.com/
- **Issues**: https://github.com/ibiface/paracle/issues
- **Email**: dev@ibiface.com

---

## Related Guides

- [GOVERNANCE.md](../.parac/GOVERNANCE.md) - Governance protocol
- [current_state.yaml](../.parac/memory/context/current_state.yaml) - State tracking
- [roadmap.yaml](../.parac/roadmap/roadmap.yaml) - Strategic roadmap
- [PRE_FLIGHT_CHECKLIST.md](../.parac/PRE_FLIGHT_CHECKLIST.md) - Task validation
