# Governance Enforcement Design

> **Status**: Proposed | **Priority**: CRITICAL | **Phase**: 10 | **Date**: 2026-01-07

## Problem Statement

Paracle has comprehensive governance documentation and infrastructure, but **enforcement is weak**. This creates a gap between documented practices and reality:

### Current Issues

1. **Manual Logging** - Agents must remember to log actions manually
2. **No Automatic State Updates** - current_state.yaml requires manual editing
3. **Weak AI Agent Compliance** - AI assistants don't consistently follow .parac/ rules
4. **No Validation Gates** - Structure violations aren't caught
5. **Optional Governance** - Can be bypassed entirely

### Impact

- **Dogfooding fails** - We don't follow our own rules
- **Trust erosion** - Documentation doesn't match reality
- **Poor community adoption** - If creators don't use it, why should users?
- **Governance theater** - Looks good on paper, doesn't work in practice

---

## Solution: 5-Layer Enforcement Model

### Layer 1: Automatic Logging (CRITICAL)

**Make logging automatic, not manual.**

#### Implementation

```python
# packages/paracle_core/governance/auto_logger.py

class AutomaticGovernanceLogger:
    """Automatic logging via decorators and context managers."""

    @staticmethod
    def log_agent_action(agent_type: str):
        """Decorator for automatic action logging."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start = datetime.now()

                try:
                    result = await func(*args, **kwargs)

                    # Auto-log success
                    logger = get_governance_logger()
                    logger.log(
                        GovernanceActionType.from_function(func),
                        f"{func.__name__} completed",
                        agent=agent_type,
                        details={
                            "duration": (datetime.now() - start).total_seconds(),
                            "args": sanitize_args(args, kwargs),
                        }
                    )

                    return result

                except Exception as e:
                    # Auto-log failure
                    logger.log(
                        GovernanceActionType.ERROR,
                        f"{func.__name__} failed: {str(e)}",
                        agent=agent_type,
                    )
                    raise

            return wrapper
        return decorator


# Usage in code
@AutomaticGovernanceLogger.log_agent_action("CoderAgent")
async def implement_feature(spec: FeatureSpec) -> Implementation:
    """Implement a feature - AUTO-LOGGED."""
    # ... implementation ...
    pass
```

#### Integration Points

```python
# packages/paracle_orchestration/executor.py

class AgentExecutor:
    """Execute agents with automatic logging."""

    async def execute(self, agent: Agent, task: Task) -> Result:
        """Execute agent - ALL actions auto-logged."""

        with governance.session(agent=agent.id):
            # Session automatically logs start/end
            result = await self._run_agent(agent, task)

            # Automatic logging happens via decorators
            # No manual logging needed!

            return result
```

**Benefits**:
- ✅ Zero manual logging required
- ✅ Complete audit trail guaranteed
- ✅ Works across all agents
- ✅ Captures successes AND failures

---

### Layer 2: Automatic State Management (HIGH PRIORITY)

**Make current_state.yaml update automatically.**

#### Implementation

```python
# packages/paracle_core/governance/state_manager.py

class AutomaticStateManager:
    """Automatic state synchronization."""

    def __init__(self, parac_root: Path):
        self.state_file = parac_root / "memory" / "context" / "current_state.yaml"
        self.roadmap_file = parac_root / "roadmap" / "roadmap.yaml"

    async def on_deliverable_completed(
        self,
        deliverable_id: str,
        agent: str,
        phase: str,
    ) -> None:
        """Auto-update state when deliverable completes."""

        # 1. Load current state
        state = self._load_state()

        # 2. Mark deliverable as complete
        state['current_phase']['completed'].append(deliverable_id)
        state['current_phase']['in_progress'] = [
            d for d in state['current_phase']['in_progress']
            if d != deliverable_id
        ]

        # 3. Recalculate progress
        roadmap = self._load_roadmap()
        phase_data = roadmap['phases'][phase]
        total = len(phase_data['deliverables'])
        completed = len([d for d in phase_data['deliverables'] if d['status'] == 'completed'])
        state['current_phase']['progress'] = int((completed / total) * 100)

        # 4. Add to recent_updates
        state['recent_updates'].insert(0, {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'update': f"{deliverable_id} COMPLETE",
            'agent': agent,
            'impact': "Phase progress updated",
        })

        # 5. Save atomically
        self._save_state(state)

        # 6. Auto-log the state change
        logger = get_governance_logger()
        logger.log(
            GovernanceActionType.UPDATE,
            f"Auto-updated state: {deliverable_id} completed",
            agent=agent,
        )


# Integration with agent execution
class AgentExecutor:
    async def execute(self, agent: Agent, task: Task) -> Result:
        result = await self._run_agent(agent, task)

        # Auto-update state if task completes a deliverable
        if task.deliverable_id:
            await state_manager.on_deliverable_completed(
                deliverable_id=task.deliverable_id,
                agent=agent.name,
                phase=task.phase,
            )

        return result
```

**Benefits**:
- ✅ State always accurate
- ✅ Roadmap and state synchronized
- ✅ Progress tracking automatic
- ✅ Human review optional, not required

---

### Layer 3: AI Agent Compliance Engine (CRITICAL FOR COMMUNITY)

**Force AI assistants to respect .parac/ structure.**

#### Implementation

```python
# packages/paracle_core/governance/ai_compliance.py

class AIAgentComplianceEngine:
    """Enforce .parac/ compliance for AI assistants."""

    def __init__(self, parac_root: Path):
        self.parac_root = parac_root
        self.rules = self._load_compliance_rules()

    def _load_compliance_rules(self) -> dict:
        """Load mandatory compliance rules."""
        return {
            "file_placement": {
                "operational_data": ".parac/memory/data/*.db",
                "logs": ".parac/memory/logs/*.log",
                "knowledge": ".parac/memory/knowledge/*.md",
                "decisions": ".parac/roadmap/decisions.md",
            },
            "mandatory_reads": [
                ".parac/GOVERNANCE.md",
                ".parac/memory/context/current_state.yaml",
                ".parac/roadmap/roadmap.yaml",
            ],
            "mandatory_logs": [
                "After EVERY agent execution",
                "After file changes",
                "After decisions",
            ],
        }

    async def validate_action(
        self,
        action: ProposedAction,
        ai_agent: str,  # "GitHub Copilot", "Claude", etc.
    ) -> ValidationResult:
        """Validate AI agent action before execution."""

        violations = []

        # Check file placement
        if action.creates_file:
            expected = self._get_expected_location(action.file_type)
            if action.file_path != expected:
                violations.append(
                    Violation(
                        type="file_placement",
                        severity="ERROR",
                        message=f"File should be at {expected}, not {action.file_path}",
                        rule="See .parac/STRUCTURE.md for correct locations",
                    )
                )

        # Check mandatory reads
        if action.is_implementation:
            for required_file in self.rules["mandatory_reads"]:
                if required_file not in action.files_read:
                    violations.append(
                        Violation(
                            type="missing_context",
                            severity="WARNING",
                            message=f"Should read {required_file} before implementation",
                            rule="See .parac/GOVERNANCE.md Rule 1",
                        )
                    )

        # Check logging
        if action.is_implementation and not action.includes_logging:
            violations.append(
                Violation(
                    type="missing_logging",
                    severity="ERROR",
                    message="Must log action to .parac/memory/logs/agent_actions.log",
                    rule="See .parac/GOVERNANCE.md Logging section",
                )
            )

        return ValidationResult(
            allowed=len([v for v in violations if v.severity == "ERROR"]) == 0,
            violations=violations,
            ai_agent=ai_agent,
        )
```

#### Integration with IDE Extensions

```python
# packages/paracle_ide/vscode_extension.py

class VSCodeExtension:
    """VS Code extension with compliance enforcement."""

    async def on_file_save(self, file_path: Path):
        """Validate file placement on save."""

        # Check if file is in .parac/
        if ".parac" in str(file_path):
            result = await compliance_engine.validate_file_placement(file_path)

            if not result.valid:
                # Show error in VS Code
                vscode.window.showErrorMessage(
                    f"❌ File placement violation: {result.violation_message}\n"
                    f"Expected: {result.expected_location}\n"
                    f"See .parac/STRUCTURE.md for rules"
                )

                # Offer to move file
                if await vscode.window.showInformationMessage(
                    "Auto-fix file location?",
                    "Yes", "No"
                ) == "Yes":
                    await self.move_file_to_correct_location(
                        file_path,
                        result.expected_location
                    )
```

**Benefits**:
- ✅ Real-time validation in IDE
- ✅ AI agents can't create files in wrong places
- ✅ Automatic corrections offered
- ✅ Works across all IDEs (VS Code, Cursor, Windsurf, etc.)

---

### Layer 4: Pre-Commit Validation Hooks (ENFORCEMENT)

**Catch violations before they enter git.**

#### Implementation

```python
# .parac/tools/hooks/validate-structure.py

#!/usr/bin/env python3
"""Pre-commit hook: Validate .parac/ structure."""

import sys
from pathlib import Path
from paracle_core.governance import StructureValidator

def main():
    """Validate .parac/ structure before commit."""

    validator = StructureValidator(Path(".parac"))
    result = validator.validate_all()

    if not result.valid:
        print("❌ .parac/ structure violations detected:")
        print()

        for violation in result.violations:
            print(f"  [{violation.severity}] {violation.file}")
            print(f"    {violation.message}")
            print(f"    Expected: {violation.expected_location}")
            print()

        print("Fix violations before committing.")
        print("Run: paracle validate structure --fix")
        return 1

    print("✅ .parac/ structure validated")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

```bash
# .parac/tools/hooks/install-hooks.sh

#!/bin/bash
# Install governance validation hooks

HOOKS_DIR=".git/hooks"
PARAC_HOOKS=".parac/tools/hooks"

# Install pre-commit hook
cp "$PARAC_HOOKS/validate-structure.py" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Governance hooks installed"
echo "  - Pre-commit: Structure validation"
```

**Benefits**:
- ✅ Violations blocked at commit time
- ✅ Can't commit without validation
- ✅ Automatic enforcement
- ✅ Works for all developers

---

### Layer 5: Continuous Monitoring & Auto-Repair (ADVANCED)

**Background process that maintains .parac/ integrity.**

#### Implementation

```python
# packages/paracle_core/governance/monitor.py

class GovernanceMonitor:
    """Background monitor for .parac/ integrity."""

    def __init__(self, parac_root: Path):
        self.parac_root = parac_root
        self.watcher = FileSystemWatcher(parac_root)

    async def start(self):
        """Start monitoring .parac/ for violations."""

        async for event in self.watcher:
            if event.type == "file_created":
                await self._validate_new_file(event.file_path)
            elif event.type == "file_modified":
                await self._validate_file_change(event.file_path)

    async def _validate_new_file(self, file_path: Path):
        """Validate newly created file."""

        result = await compliance_engine.validate_file_placement(file_path)

        if not result.valid:
            # Auto-fix if possible
            if result.can_auto_fix:
                logger.warning(
                    f"Auto-moving {file_path} to {result.expected_location}"
                )
                await self._move_file(file_path, result.expected_location)
            else:
                # Alert user
                logger.error(
                    f"❌ Structure violation: {file_path}\n"
                    f"Expected: {result.expected_location}\n"
                    f"See .parac/STRUCTURE.md"
                )
```

```bash
# Start monitor as background process
paracle governance monitor --auto-fix
```

**Benefits**:
- ✅ Real-time monitoring
- ✅ Automatic corrections
- ✅ Alerts on violations
- ✅ Maintains integrity 24/7

---

## Implementation Roadmap

### Phase 1: Critical Foundation (Week 1-2)

**Goal**: Make logging and state updates automatic

1. ✅ Implement `AutomaticGovernanceLogger`
2. ✅ Add decorators to all agent operations
3. ✅ Implement `AutomaticStateManager`
4. ✅ Hook into agent executor
5. ✅ Test with dogfooding

**Success Criteria**:
- All agent actions auto-logged
- State updates automatically
- No manual Add-Content needed

### Phase 2: AI Compliance Engine (Week 2-3)

**Goal**: Force AI assistants to respect .parac/

1. ✅ Implement `AIAgentComplianceEngine`
2. ✅ Add validation rules from STRUCTURE.md
3. ✅ Integrate with MCP server
4. ✅ Add IDE extension hooks
5. ✅ Test with multiple AI assistants

**Success Criteria**:
- File placement errors caught
- AI agents can't violate structure
- Real-time validation in IDE

### Phase 3: Pre-Commit Validation (Week 3)

**Goal**: Block violations at commit time

1. ✅ Create pre-commit hook
2. ✅ Add structure validation
3. ✅ Add auto-fix suggestions
4. ✅ Document hook installation
5. ✅ Add to `paracle init`

**Success Criteria**:
- Violations blocked at commit
- Auto-fix works
- Installed by default

### Phase 4: Continuous Monitoring (Week 4)

**Goal**: 24/7 integrity maintenance

1. ✅ Implement `GovernanceMonitor`
2. ✅ Add file system watcher
3. ✅ Add auto-repair logic
4. ✅ Add monitoring dashboard
5. ✅ Test with production loads

**Success Criteria**:
- Violations detected in real-time
- Auto-repair works
- Monitoring dashboard active

---

## Enforcement Levels

### Level 1: SOFT (Current - Broken)

- Documentation only
- Manual compliance
- Optional validation
- **Problem**: Ignored by everyone

### Level 2: MEDIUM (Phase 1-2)

- Automatic logging
- Automatic state updates
- Real-time warnings in IDE
- **Better**: Harder to ignore

### Level 3: HARD (Phase 3)

- Pre-commit validation
- Blocks violations at commit
- Can't push invalid structure
- **Good**: Enforced by git

### Level 4: FORTRESS (Phase 4)

- Continuous monitoring
- Automatic repairs
- Real-time alerts
- Read-only for invalid changes
- **Best**: Self-healing system

---

## Configuration

```yaml
# .parac/config/governance.yaml

governance:
  enforcement_level: hard  # soft | medium | hard | fortress

  automatic_logging:
    enabled: true
    log_successes: true
    log_failures: true
    include_stack_traces: true

  automatic_state:
    enabled: true
    sync_on_deliverable: true
    sync_on_phase_change: true
    validate_before_save: true

  ai_compliance:
    enabled: true
    block_violations: true
    auto_fix: ask  # never | ask | always
    show_warnings: true

  pre_commit:
    enabled: true
    block_on_error: true
    auto_fix: ask

  monitoring:
    enabled: false  # Advanced users only
    auto_repair: false
    alert_on_violation: true
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/governance/test_auto_logger.py

async def test_automatic_logging():
    """Test automatic action logging."""

    @AutomaticGovernanceLogger.log_agent_action("TestAgent")
    async def test_function():
        return "success"

    result = await test_function()

    # Verify auto-logged
    logs = get_governance_logger().get_recent(1)
    assert len(logs) == 1
    assert logs[0].agent == "TestAgent"
    assert logs[0].action == "IMPLEMENTATION"
    assert "test_function completed" in logs[0].description
```

### Integration Tests

```python
# tests/integration/governance/test_enforcement.py

async def test_file_placement_enforcement():
    """Test file placement violations are caught."""

    # Try to create file in wrong location
    wrong_path = parac_root / "costs.db"  # Should be in memory/data/

    with pytest.raises(StructureViolationError) as exc:
        await create_file(wrong_path, content="test")

    assert "Expected: .parac/memory/data/costs.db" in str(exc.value)
```

### Dogfooding Tests

```python
# tests/dogfooding/test_governance_compliance.py

def test_our_own_parac_compliant():
    """Test that OUR .parac/ follows the rules."""

    validator = StructureValidator(Path(".parac"))
    result = validator.validate_all()

    assert result.valid, f"Violations: {result.violations}"

    # We must eat our own dog food!
```

---

## Success Metrics

### Before (Current - Broken)

- ❌ Manual logging: ~30% compliance
- ❌ State updates: Frequently stale
- ❌ File placement: Violations common
- ❌ AI agent compliance: ~40%
- ❌ Overall trust: Low

### After (Phase 4 Complete)

- ✅ Automatic logging: 100% compliance
- ✅ State updates: Always current
- ✅ File placement: 100% validated
- ✅ AI agent compliance: ~95%
- ✅ Overall trust: High

---

## Community Adoption Strategy

### For Small Projects

```yaml
# .parac/project.yaml

governance:
  enforcement_level: soft  # Start gentle

  lite_mode: true  # Minimal .parac/ structure

  required_files:
    - roadmap/roadmap.yaml
    - memory/logs/agent_actions.log
    - policies/CODE_STYLE.md
```

### For Medium Projects

```yaml
governance:
  enforcement_level: medium  # More structure

  standard_mode: true  # Full .parac/ structure

  automatic_logging: true
  automatic_state: true
```

### For Enterprise Projects

```yaml
governance:
  enforcement_level: fortress  # Maximum enforcement

  enterprise_mode: true

  continuous_monitoring: true
  audit_trail: true
  iso_42001_compliance: true
```

---

## Migration Path

### Existing Projects

```bash
# Step 1: Audit current state
paracle governance audit

# Step 2: Fix violations
paracle governance fix --auto

# Step 3: Enable enforcement
paracle governance enable --level medium

# Step 4: Verify
paracle governance verify
```

### New Projects

```bash
# Enforcement enabled by default
paracle init my-project

# Creates .parac/ with hooks pre-installed
# Enforcement level: medium by default
```

---

## ADR: Make Governance Mandatory

**ADR-020: Mandatory Governance Enforcement**

**Date**: 2026-01-07
**Status**: Proposed
**Priority**: CRITICAL

### Context

Paracle's governance model is comprehensive but not enforced. This creates a gap between documentation and reality, undermining trust and adoption.

### Decision

**Make governance enforcement MANDATORY for v1.0.0:**

1. Automatic logging (no manual logging allowed)
2. Automatic state management
3. Pre-commit validation (blocks violations)
4. AI compliance engine (real-time validation)
5. Optional continuous monitoring (advanced)

### Consequences

**Positive**:
- ✅ Governance actually works
- ✅ .parac/ becomes true source of truth
- ✅ Community trusts the framework
- ✅ Dogfooding succeeds

**Negative**:
- ❌ Learning curve steeper
- ❌ More complex internally
- ❌ Migration effort for existing projects

**Mitigation**:
- Progressive disclosure (lite mode)
- Excellent documentation
- Auto-fix for violations
- Migration tools

### Implementation

Phase 10 (current phase) - Weeks 37-42

---

## Questions for Discussion

1. **Enforcement Level**: Should we start with `soft`, `medium`, or `hard`?
   - **Recommendation**: `medium` for v1.0.0 (auto-logging + pre-commit)

2. **Migration**: How to migrate existing projects?
   - **Recommendation**: `paracle governance migrate` command with auto-fix

3. **Lite Mode**: Should lite mode have weaker enforcement?
   - **Recommendation**: Yes - `soft` for lite, `medium` for standard, `hard` for enterprise

4. **Community Pushback**: What if users resist enforcement?
   - **Recommendation**: Make it configurable but encourage best practices

---

## Next Steps

1. **Review this design** - Get feedback from PM Agent, Architect Agent
2. **Create ADR-020** - Document decision formally
3. **Update roadmap** - Add to Phase 10 deliverables
4. **Implement Phase 1** - Automatic logging + state management
5. **Test with dogfooding** - Use it ourselves first
6. **Roll out to community** - v1.0.0 release

---

## References

- [GOVERNANCE.md](../GOVERNANCE.md) - Current governance protocol
- [STRUCTURE.md](../STRUCTURE.md) - File placement rules
- [current_state.yaml](../memory/context/current_state.yaml) - Project state
- [roadmap.yaml](../roadmap/roadmap.yaml) - Roadmap
- [GovernanceLogger](../../packages/paracle_core/governance/logger.py) - Current logger

---

**Last Updated**: 2026-01-07
**Version**: 1.0
**Status**: Proposed - Awaiting Review
