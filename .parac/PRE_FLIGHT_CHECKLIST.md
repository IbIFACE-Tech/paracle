# 🚨 MANDATORY PRE-FLIGHT CHECKLIST

> **Purpose**: Ensure you work on the RIGHT task, at the RIGHT time, with the RIGHT priority.
> **Time Required**: ~4 minutes
> **Frequency**: Before EVERY implementation task

---

## Why This Checklist Exists

This project uses **Paracle to build Paracle** (dogfooding). The `.parac/` directory is the **single source of truth** for all project governance, decisions, and state. Before making ANY changes, you MUST validate against this source of truth to avoid:

- ❌ Working on wrong phase tasks
- ❌ Duplicating work or blocking others
- ❌ Missing critical dependencies
- ❌ Violating governance policies
- ❌ Breaking production-ready code (v1.0.0 - 95/100 security score)

---

## 📋 The Checklist

### ✅ Step 1: Read Governance Rules (30 seconds)

**File**: [`.parac/GOVERNANCE.md`](.parac/GOVERNANCE.md)

**What to Check**:
- Understand dogfooding context (Paracle develops Paracle)
- Review the 3 core governance rules (Traçabilité, Immutabilité, Synchronisation)
- Confirm you'll update `.parac/` files after work

**Why**: Establishes the foundation - `.parac/` is the source of truth.

---

### ✅ Step 2: Check Current Project State (1 minute)

**File**: [`.parac/memory/context/current_state.yaml`](.parac/memory/context/current_state.yaml)

**What to Check**:
```yaml
# Current state as of 2026-01-08:
project:
  phase: phase_10              # ← What phase are we in?
  status: in_progress          # ← Is phase active?
  version: 1.0.0              # ← Current version

current_phase:
  id: phase_10
  name: "Governance & v1.0 Release"
  progress: 95%               # ← How far along?
  status: in_progress
  focus: |
    - Complete 5-layer governance system ✅
    - Security audit complete (95/100) ✅
    - Production deployment ready ✅
    - Integration testing
    - Performance benchmarking
    - v1.0.0 release preparation

  completed: [...]            # ← What's done?
  in_progress: [...]          # ← What's being worked on?
```

**Questions to Answer**:
1. What phase is the project in? → **phase_10**
2. What is the current progress? → **95%**
3. What's currently in progress? → Check `in_progress` list
4. Is your task aligned with current focus?

**Why**: Prevents working on wrong phase or duplicating active work.

---

### ✅ Step 3: Consult Roadmap (1 minute)

**File**: [`.parac/roadmap/roadmap.yaml`](.parac/roadmap/roadmap.yaml)

**What to Check**:
```yaml
current_phase: phase_10

phases:
  - id: phase_10
    name: "Governance & v1.0 Release"
    status: in_progress
    deliverables:
      - name: "Complete governance system"
        status: completed
        priority: P0
      - name: "Security audit & compliance"
        status: completed
        priority: P0
      - name: "Integration testing"
        status: in_progress
        priority: P1
      # ... more deliverables

    priorities:
      - P0: Security & Governance (COMPLETE)
      - P1: Testing & Validation (IN PROGRESS)
      - P2: Documentation finalization
      - P3: v1.0.0 Release preparation
```

**Questions to Answer**:
1. Is your task listed in current phase deliverables? **YES/NO**
2. What's the priority of your task? **P0/P1/P2/P3**
3. Are dependencies completed? **Check status**
4. Does task align with phase focus?

**CRITICAL**: If task is NOT in roadmap → **STOP** → Discuss with PM Agent first.

**Why**: Ensures alignment with strategic priorities and dependencies.

---

### ✅ Step 4: Check Open Questions & Blockers (30 seconds)

**File**: [`.parac/memory/context/open_questions.md`](.parac/memory/context/open_questions.md)

**What to Check**:
- Are there open questions related to your task?
- Are there known blockers you should be aware of?
- Has someone already asked about this feature/issue?

**Why**: Avoids duplicate work and identifies known blockers early.

---

### ✅ Step 5: VALIDATE Your Task (30 seconds)

**Answer ALL these questions**:

```
Task Validation Checklist:
□ Is task in roadmap.yaml deliverables for current phase?
□ Is task priority appropriate (P0 > P1 > P2 > P3)?
□ Are all dependencies completed? (Check roadmap status)
□ Is task NOT already in current_state.yaml in_progress?
□ Does task align with phase focus?
□ Are there no blocking open questions?
```

**Decision Matrix**:

| Scenario                  | Action                                     |
| ------------------------- | ------------------------------------------ |
| ✅ All checks pass         | **PROCEED** to Step 6                      |
| ❌ Task NOT in roadmap     | **STOP** - Add to roadmap first (PM Agent) |
| ❌ Dependencies incomplete | **STOP** - Complete dependencies first     |
| ❌ Already in progress     | **STOP** - Check with team/agent owner     |
| ❌ Wrong phase             | **STOP** - Work on current phase tasks     |
| ⚠️  Priority mismatch      | **DISCUSS** - Confirm with PM Agent        |

**Why**: Gate-check before investing time in implementation.

---

### ✅ Step 6: Select Agent to Execute (30 seconds)

**File**: [`.parac/agents/manifest.yaml`](.parac/agents/manifest.yaml)

**Agent Selection Guide**:

| Task Type                  | Agent to Run       | Spec File                        |
| -------------------------- | ------------------ | -------------------------------- |
| New feature implementation | `coder`            | `agents/specs/coder.md`          |
| Architecture design        | `architect`        | `agents/specs/architect.md`      |
| Bug fix                    | `coder` + `tester` | Both spec files                  |
| Documentation              | `documenter`       | `agents/specs/documenter.md`     |
| Code review                | `reviewer`         | `agents/specs/reviewer.md`       |
| Test creation              | `tester`           | `agents/specs/tester.md`         |
| Project planning           | `pm`               | `agents/specs/pm.md`             |
| Release management         | `releasemanager`   | `agents/specs/releasemanager.md` |
| Security audit             | `security`         | `agents/specs/security.md`       |

**Read Agent Spec**: Always read the full spec from `.parac/agents/specs/{agent}.md` to understand:
- Agent's responsibilities
- Agent's assigned skills (see `.parac/agents/SKILL_ASSIGNMENTS.md`)
- Agent's execution patterns
- Agent's output expectations

**Execution Command**:
```bash
paracle agent run {agent} --task "Your task description"

# Example:
paracle agent run coder --task "Implement user authentication feature"
```

**Why**: Ensures the right specialized agent handles the task.

---

### ✅ Step 7: Check Policies (30 seconds)

**Files**: [`.parac/policies/`](.parac/policies/)

**Required Policy Reviews**:

| Policy       | File              | When to Check           |
| ------------ | ----------------- | ----------------------- |
| Code Style   | `CODE_STYLE.md`   | Before ANY code         |
| Testing      | `TESTING.md`      | Before writing tests    |
| Security     | `SECURITY.md`     | Security-sensitive code |
| Git Workflow | `GIT_WORKFLOW.md` | Before commits          |

**Key Standards (Quick Reference)**:
- **Python**: 3.10+, type hints, Pydantic v2, Google-style docstrings
- **Architecture**: Hexagonal (ports & adapters)
- **Testing**: pytest, 80%+ coverage, unit + integration
- **Security**: OWASP Top 10, ISO 27001/42001, SOC2 compliant
- **Git**: Conventional commits, semantic versioning

**Why**: Ensures compliance with project standards from the start.

---

## 📝 POST-WORK CHECKLIST (MANDATORY)

After completing your task, you MUST:

### ✅ Step 8: Log Your Action (Required)

**File**: [`.parac/memory/logs/agent_actions.log`](.parac/memory/logs/agent_actions.log)

**Format**:
```
[TIMESTAMP] [AGENT] [ACTION] Description with file paths
```

**Example**:
```
[2026-01-09 10:30:00] [CoderAgent] [IMPLEMENTATION] Implemented authentication in packages/paracle_api/auth.py
[2026-01-09 11:00:00] [TesterAgent] [TEST] Added unit tests for auth in tests/unit/test_auth.py
[2026-01-09 11:30:00] [ReviewerAgent] [REVIEW] Reviewed PR #45 - authentication feature
```

**Action Types**:
- `IMPLEMENTATION` - Code implementation
- `TEST` - Test creation/modification
- `BUGFIX` - Bug correction
- `REFACTORING` - Code refactoring
- `REVIEW` - Code review
- `DOCUMENTATION` - Documentation update
- `DECISION` - Important decision
- `PLANNING` - Planning/roadmap updates

**Why**: Traceability - every change is logged for audit and context.

---

### ✅ Step 9: Update State (If Milestone Reached)

**File**: [`.parac/memory/context/current_state.yaml`](.parac/memory/context/current_state.yaml)

**Update When**:
- A deliverable is completed
- Phase progress changes significantly (e.g., 75% → 80%)
- Moving from `in_progress` to `completed`

**What to Update**:
```yaml
current_phase:
  progress: 95%  # ← Update percentage
  completed:
    - deliverable_name  # ← Add completed item
  in_progress:
    - active_task  # ← Update active work
```

**Also Update** (if applicable):
- `decisions.md` - For important decisions
- `open_questions.md` - Mark resolved questions
- `memory/knowledge/*.md` - Add learnings

**Why**: Keeps source of truth synchronized with reality.

---

## 🎯 Quick Reference Card

**Before EVERY task:**
1. ✅ Read GOVERNANCE.md (30s)
2. ✅ Check current_state.yaml (1m)
3. ✅ Consult roadmap.yaml (1m)
4. ✅ Check open_questions.md (30s)
5. ✅ VALIDATE task alignment (30s)
6. ✅ Select agent & read spec (30s)
7. ✅ Check policies (30s)

**After EVERY task:**
8. ✅ Log action to agent_actions.log (Required)
9. ✅ Update current_state.yaml (If milestone)

**Total Time**: ~4 minutes (saves hours of wasted work)

---

## ❌ Common Mistakes to Avoid

1. **Skipping this checklist** → Working on wrong priorities
2. **Not reading current_state.yaml** → Duplicating work
3. **Ignoring roadmap.yaml** → Working ahead/behind
4. **Not validating task** → Wasted implementation time
5. **Forgetting to log** → Lost traceability
6. **Not updating state** → Source of truth becomes stale

---

## 🔗 Related Files

- [GOVERNANCE.md](.parac/GOVERNANCE.md) - Governance protocol
- [STRUCTURE.md](.parac/STRUCTURE.md) - `.parac/` folder structure
- [current_state.yaml](.parac/memory/context/current_state.yaml) - Current project state
- [roadmap.yaml](.parac/roadmap/roadmap.yaml) - Full roadmap
- [open_questions.md](.parac/memory/context/open_questions.md) - Open questions
- [agents/manifest.yaml](.parac/agents/manifest.yaml) - Available agents
- [SKILL_ASSIGNMENTS.md](.parac/agents/SKILL_ASSIGNMENTS.md) - Agent skills
- [policies/](.parac/policies/) - All policies

---

## 📞 Questions?

- **Project stuck?** → Check `open_questions.md` or ask PM Agent
- **Unclear priority?** → Consult `roadmap.yaml` priorities
- **Policy question?** → Read relevant policy in `.parac/policies/`
- **Technical decision?** → Review `roadmap/decisions.md` (ADRs)

---

**Remember**: This checklist exists to **save you time**, not waste it. 4 minutes now prevents hours of rework later.

**Status**: Active | **Version**: 1.0 | **Last Updated**: 2026-01-09
