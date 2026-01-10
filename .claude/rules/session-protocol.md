# Session Protocol

## Session Start Ritual

At the beginning of each work session, establish context:

```text
SESSION START
=============
Project: Paracle Multi-Agent Framework
Phase: [Current phase from .parac/memory/context/current_state.yaml]
Focus: [Current task or feature]

Source of Truth:
- .parac/ - Project governance
- .roadmap/ - Complete roadmap
- content/docs/ - Architecture documentation

Continuing from previous state.
I will not reintroduce rejected decisions (see .parac/roadmap/decisions.md).
```

---

## Context Loading Order

1. **Read current state**

   ```text
   .parac/memory/context/current_state.yaml
   ```

2. **Check recent decisions**

   ```text
   .parac/roadmap/decisions.md (last 5 entries)
   ```

3. **Review open questions**

   ```text
   .parac/memory/context/open_questions.md
   ```

4. **Check tech debt**

   ```text
   .parac/memory/context/tech_debt.md
   ```

---

## During Session

### Progress Tracking

After completing significant work:

```text
CHECKPOINT
==========
Completed:
- [Task 1]
- [Task 2]

Decisions Made:
- [Decision 1]: [Rationale]

Open Questions:
- [Question 1]

Next Steps:
- [Step 1]
- [Step 2]
```

### When Stuck

```text
BLOCKED
=======
Task: [What I'm trying to do]
Blocker: [What's preventing progress]
Attempted:
- [Approach 1]: [Why it failed]
- [Approach 2]: [Why it failed]

Need:
- [Information/decision/clarification needed]
```

---

## Session End Ritual

Before ending a session, produce a summary:

```markdown
## Session Summary: [Date/Identifier]

### Accomplished
- [Major accomplishment 1]
- [Major accomplishment 2]

### Decisions Made
| Decision | Rationale | Impact |
|----------|-----------|--------|
| [D1] | [Why] | [What it affects] |
| [D2] | [Why] | [What it affects] |

### Rejected Approaches
| Approach | Reason for Rejection |
|----------|---------------------|
| [A1] | [Why rejected] |
| [A2] | [Why rejected] |

### Open Questions
1. [Question 1] - Priority: [High/Medium/Low]
2. [Question 2] - Priority: [High/Medium/Low]

### Technical Debt Incurred
- [Debt 1]: [Why, and when to address]

### Next Session Focus
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

### Files Modified
- `path/to/file1.py` - [Brief description]
- `path/to/file2.py` - [Brief description]
```

---

## Context Handoff

When transitioning between sessions or contexts:

```text
HANDOFF DOCUMENT
================

## Current State
[Brief description of where things stand]

## Critical Context
- [Key fact 1 that must not be forgotten]
- [Key fact 2 that must not be forgotten]

## In-Progress Work
- [Task]: [Status, what's done, what remains]

## Gotchas
- [Non-obvious thing 1 that could cause confusion]
- [Non-obvious thing 2]

## Do Not
- [Thing to avoid 1]
- [Thing to avoid 2]

## Resume From
[Exact point to continue from]
```

---

## Emergency Recovery

If context is lost or confused:

```text
RECOVERY PROTOCOL
=================

1. Read: .parac/memory/context/current_state.yaml
2. Read: .parac/roadmap/roadmap.yaml (current phase)
3. Read: .roadmap/ROADMAP_GLOBALE.yaml (big picture)
4. Check: git log --oneline -20 (recent changes)
5. Check: git status (current state)

DO NOT proceed until context is re-established.
ASK for clarification if state is ambiguous.
```

---

## Cognitive Load Management

### When Task is Large

Break into subtasks with explicit boundaries:

```text
TASK DECOMPOSITION
==================

Main Task: [Description]

Subtasks:
1. [ ] [Subtask 1] - Scope: [boundaries]
2. [ ] [Subtask 2] - Scope: [boundaries]
3. [ ] [Subtask 3] - Scope: [boundaries]

Current Focus: Subtask [N]
Out of Scope for Now: [Everything else]
```

### When Confused

```text
CONFUSION CHECKPOINT
====================

What I think I'm doing: [Description]
What I'm uncertain about: [Uncertainty]
What I need to clarify: [Question]

PAUSE until clarity is achieved.
```

---

## Quality Gates Per Session

Before ending any session:

```text
SESSION QUALITY CHECK
=====================

[ ] All code changes have tests
[ ] No new linting errors introduced
[ ] Documentation updated if needed
[ ] Decisions documented in decisions.md
[ ] Open questions captured
[ ] Tech debt logged if incurred
[ ] Session summary produced
[ ] Next steps identified
```
