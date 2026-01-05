# Roadmap and State Synchronization

## Problem

The `.parac/roadmap/roadmap.yaml` and `.parac/memory/context/current_state.yaml` files can drift apart over time because they're updated independently. This leads to:

- **Misaligned phase definitions** (different names, statuses, completion percentages)
- **Missing deliverables** in one file vs the other
- **Inconsistent metrics** between files
- **Confusion** about actual project status

## Solution

The `paracle sync --roadmap` command now automatically detects and reports misalignments between the two files.

### Usage

```bash
# Full synchronization (includes roadmap check)
paracle sync

# Only check roadmap alignment (skip git/metrics/manifest)
paracle sync --no-git --no-metrics --no-manifest --roadmap

# Check with automatic fixes for safe mismatches
paracle sync --auto-fix

# Dry-run: detect issues without making changes
paracle sync --no-auto-fix
```

### What Gets Checked

1. **Phase Alignment**
   - ✅ Phase IDs match between files
   - ✅ Phase names are consistent
   - ✅ Status (planned/in_progress/completed) aligns
   - ✅ Completion percentages are within 10% tolerance

2. **Deliverables**
   - ✅ Deliverables listed in roadmap appear in state
   - ⚠️  Extra deliverables in state (suggests adding to roadmap)

3. **Metrics**
   - ✅ Test coverage is consistent
   - ✅ Test counts match (or close)

### Output Example

```bash
$ paracle sync

Synchronizing .parac/ state...

Changes made:
  OK Git info updated: last_commit updated
  OK Metrics updated: python_files: 77 → 130
  OK Regenerated manifest.yaml

Roadmap Alignment Warnings:
  ⚠  Phase name mismatch: roadmap='Orchestration & API', state='Orchestration Engine Core'
  ⚠  Phase phase_4 completion mismatch: roadmap=30%, state=75%

Suggestions:
  💡 Consider updating roadmap.yaml status to match actual progress
  💡 Synchronize completion percentages between files

OK Synchronization complete.
```

### Auto-Fix Behavior

When using `--auto-fix`, the system will automatically fix **safe** mismatches:

**Safe fixes (auto-applied):**
- Update phase name in state to match roadmap
- Sync snapshot_date

**Manual review required:**
- Phase status mismatches (suggests updating roadmap)
- Completion percentage differences (requires decision)
- Missing/extra deliverables (suggests manual sync)

### Workflow Integration

#### After Roadmap Changes

```bash
# 1. Update roadmap.yaml manually
vim .parac/roadmap/roadmap.yaml

# 2. Sync to detect misalignments
paracle sync --roadmap

# 3. Review warnings and suggestions
# 4. Update current_state.yaml based on suggestions
vim .parac/memory/context/current_state.yaml

# 5. Verify alignment
paracle sync --roadmap
```

#### After Major Progress

```bash
# 1. Update current_state.yaml with progress
paracle session end --progress 80% --complete feature_x

# 2. Sync to check if roadmap needs updating
paracle sync --roadmap

# 3. If roadmap is outdated, update it
vim .parac/roadmap/roadmap.yaml

# 4. Verify
paracle sync --roadmap
```

### Git Hook (Automated)

You can set up a pre-commit hook to automatically check alignment:

```bash
# Install hook
cp .parac/tools/hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

The hook will:
1. Run `paracle sync --roadmap`
2. Display warnings if misalignment detected
3. Allow commit to proceed (warning only)

### Governance Update

The `GOVERNANCE.md` now includes:

```markdown
### À Chaque Session

1. Lire current_state.yaml
2. Vérifier roadmap.yaml
3. Confirmer la phase actuelle
4. **Exécuter `paracle sync --roadmap`** ← NEW

### À Chaque Changement de Phase

1. Mettre à jour roadmap.yaml
2. Mettre à jour current_state.yaml
3. **Exécuter `paracle sync --roadmap`** ← NEW
4. Résoudre les avertissements
```

### API Support

The API also supports roadmap checking:

```python
# Via Python SDK
from paracle_core.parac.roadmap_sync import sync_roadmap_and_state

result = sync_roadmap_and_state(
    parac_root=Path(".parac"),
    dry_run=True,  # Don't make changes
    auto_fix=False,
)

print(f"Warnings: {result.warnings}")
print(f"Suggestions: {result.suggestions}")
```

```bash
# Via REST API
curl -X POST http://localhost:8000/parac/sync \
  -H "Content-Type: application/json" \
  -d '{"check_roadmap": true, "auto_fix": false}'
```

### Best Practices

1. **Run sync regularly** - At least once per session
2. **Review warnings carefully** - They indicate governance drift
3. **Update both files** - Keep roadmap and state in sync
4. **Use auto-fix cautiously** - Review changes before committing
5. **Document decisions** - Update `decisions.md` when resolving conflicts

### Troubleshooting

**Q: Sync says phase not found in roadmap**
A: The `current_phase.id` in state doesn't exist in roadmap.yaml. Either add the phase to roadmap or fix the ID in state.

**Q: Completion percentages always mismatch**
A: Allow 10% tolerance. Larger differences suggest one file is outdated.

**Q: Too many warnings**
A: This indicates significant drift. Review and update both files manually, then run sync to verify.

**Q: Auto-fix changed the wrong value**
A: Auto-fix only updates state names to match roadmap. If roadmap is wrong, update roadmap manually first.

### Implementation Details

**New Files:**
- `packages/paracle_core/parac/roadmap_sync.py` - Synchronization logic
- `docs/roadmap-state-sync.md` - This documentation

**Modified Files:**
- `packages/paracle_cli/commands/parac.py` - Enhanced `sync` command
- `.parac/GOVERNANCE.md` - Updated workflow protocols

**Future Enhancements:**
- Interactive conflict resolution
- Diff view for mismatches
- Automatic roadmap generation from state
- Historical drift tracking
