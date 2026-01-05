# Pre-Flight Checklist for AI Assistants

## 🚨 MANDATORY: Before ANY Implementation Task

This checklist is **NOT OPTIONAL**. Every AI assistant working on Paracle MUST complete these steps before implementing any feature, fix, or change.

---

## ✅ Step 1: Read Governance (30 seconds)

```bash
Read: .parac/GOVERNANCE.md
```

**Questions to answer:**
- [ ] What is the dogfooding context? (Paracle develops Paracle)
- [ ] What are the 3 governance rules?
- [ ] What must be logged after actions?

**Why:** Understand the project's meta nature and traceability requirements.

---

## ✅ Step 2: Check Current State (30 seconds)

```bash
Read: .parac/memory/context/current_state.yaml
```

**Questions to answer:**
- [ ] What is the current phase? (phase_4, phase_5, etc.)
- [ ] What is the current progress? (X%)
- [ ] What is currently `in_progress`?
- [ ] What is recently `completed`?
- [ ] What is `pending`?

**Why:** Understand where the project is RIGHT NOW.

---

## ✅ Step 3: Consult Roadmap (1 minute)

```bash
Read: .parac/roadmap/roadmap.yaml
```

**Questions to answer:**
- [ ] What is the focus of the current phase?
- [ ] What are the current phase deliverables?
- [ ] What are the priorities (P0, P1, P2)?
- [ ] Is the requested task in the roadmap?
- [ ] Does it align with current phase priorities?

**Why:** Ensure you're working on the RIGHT THING at the RIGHT TIME.

---

## ✅ Step 4: Check Open Questions (30 seconds)

```bash
Read: .parac/memory/context/open_questions.md
```

**Questions to answer:**
- [ ] Are there related open questions?
- [ ] Will this task answer any questions?
- [ ] Will this task create new questions?

**Why:** Avoid working on blocked or unclear items.

---

## ✅ Step 5: Validate Task Alignment (Decision Point)

**ASK YOURSELF:**

1. **Is this task in the roadmap?**
   - ✅ YES → Proceed to Step 6
   - ❌ NO → **STOP and ask user**: "This task is not in the roadmap. Should I:
     - a) Add it to current phase?
     - b) Defer to future phase?
     - c) Proceed anyway (with justification)?"

2. **Is this task in the current phase?**
   - ✅ YES → Proceed to Step 6
   - ❌ NO → **STOP and ask user**: "This task is planned for phase X, but we're in phase Y. Should I:
     - a) Move it to current phase?
     - b) Work on current phase priorities first?
     - c) Proceed anyway (with justification)?"

3. **Is this task a current priority (P0/P1)?**
   - ✅ YES → Proceed to Step 6
   - 🟡 P2 → **WARN user**: "This is P2 priority. Higher priorities exist. Continue?"
   - ❌ NO PRIORITY → **STOP and ask user**: "This task has no priority. Should I prioritize it?"

4. **Are dependencies completed?**
   - ✅ YES → Proceed to Step 6
   - ❌ NO → **STOP and ask user**: "Dependencies incomplete: [list]. Should I:
     - a) Complete dependencies first?
     - b) Proceed with assumptions?
     - c) Mark as blocked?"

---

## ✅ Step 6: Adopt Agent Persona (30 seconds)

Based on task type, read the appropriate agent spec:

```bash
# Task Type → Agent
New feature        → .parac/agents/specs/coder.md
Architecture       → .parac/agents/specs/architect.md
Documentation      → .parac/agents/specs/documenter.md
Code review        → .parac/agents/specs/reviewer.md
Testing            → .parac/agents/specs/tester.md
Planning           → .parac/agents/specs/pm.md
```

**Questions to answer:**
- [ ] What is this agent's role?
- [ ] What are this agent's responsibilities?
- [ ] What standards must this agent follow?

**Why:** Adopt the correct persona and standards for the task.

---

## ✅ Step 7: Check Policies (30 seconds)

```bash
Read relevant: .parac/policies/
- CODE_STYLE.md    (for implementation)
- TESTING.md       (for tests)
- SECURITY.md      (for security-sensitive code)
```

**Why:** Follow project standards and best practices.

---

## ✅ Step 8: Implement with Context

**NOW you can implement!**

With full context from steps 1-7:
- Current phase and priorities
- Agent persona and standards
- Project policies
- Open questions

---

## ✅ Step 9: Log Action (MANDATORY)

After implementation:

```bash
Append to: .parac/memory/logs/agent_actions.log

Format:
[YYYY-MM-DD HH:MM:SS] [AgentName] [ACTION_TYPE] Description with file paths

Example:
[2026-01-05 10:30:00] [CoderAgent] [IMPLEMENTATION] Implemented pattern orchestrators in packages/paracle_orchestration/patterns/
```

**Why:** Traceability and audit trail.

---

## ✅ Step 10: Update State (If Significant)

If this completes a deliverable or milestone:

```bash
Update: .parac/memory/context/current_state.yaml

Move items from:
- in_progress → completed
- Update progress percentage
```

**Why:** Keep state synchronized with reality.

---

## 🔥 Quick Checklist (Copy-Paste)

```
BEFORE IMPLEMENTING:
[ ] Read GOVERNANCE.md
[ ] Check current_state.yaml (current phase, progress, in_progress)
[ ] Consult roadmap.yaml (phase focus, deliverables, priorities)
[ ] Check open_questions.md (blockers, related questions)
[ ] VALIDATE: Task in roadmap? Current phase? Priority? Dependencies?
[ ] Adopt agent persona (read specs/{agent}.md)
[ ] Check policies (CODE_STYLE, TESTING, SECURITY)

AFTER IMPLEMENTING:
[ ] Log action to agent_actions.log
[ ] Update current_state.yaml if milestone reached
[ ] Log decisions to decisions.log if applicable
```

---

## Why This Matters

### Without Pre-Flight Checklist:
❌ Work on wrong priorities
❌ Ignore phase dependencies
❌ Miss architectural decisions
❌ Create conflicts with roadmap
❌ Duplicate efforts
❌ No traceability

### With Pre-Flight Checklist:
✅ Aligned with roadmap
✅ Correct priorities
✅ Proper sequencing
✅ Full context
✅ Complete traceability
✅ Governance compliance

---

## Exception Cases

### Emergency Fixes
For critical bugs or security issues:
- Read governance + current state (Steps 1-2) → Minimum
- Implement fix
- Log action
- Add to roadmap retroactively

### User Override
If user explicitly says "I know this isn't in roadmap, do it anyway":
- Complete Steps 1-2 (governance + state)
- Note override in log
- Suggest adding to roadmap

### Exploration/Prototyping
For exploratory work or prototypes:
- Complete Steps 1-2 (governance + state)
- Mark as "exploration" in logs
- Don't update roadmap

---

## Enforcement

**This checklist is MANDATORY.**

If an AI assistant implements a task without completing this checklist:
1. The action is **invalid**
2. No credit toward progress
3. Must be redone with proper context

**The roadmap is not a suggestion. It's the plan.**

---

## Time Investment

**Total time: ~4 minutes**

Breakdown:
- Step 1 (Governance): 30s
- Step 2 (Current State): 30s
- Step 3 (Roadmap): 1m
- Step 4 (Open Questions): 30s
- Step 5 (Validation): 1m
- Step 6 (Agent Persona): 30s
- Step 7 (Policies): 30s

**ROI: Avoid hours of wasted work on wrong priorities!**

---

## FAQ

**Q: Do I really need to do this EVERY time?**
**A:** YES. The 4 minutes upfront saves hours of rework.

**Q: What if the user's request is clearly urgent?**
**A:** Still do Steps 1-2 minimum. Then implement with note.

**Q: What if I already know the roadmap?**
**A:** Roadmap changes. Always check current state.

**Q: Can I skip this for tiny tasks?**
**A:** Do Steps 1-2 minimum. Full checklist for any code change.

**Q: What if this slows me down?**
**A:** It speeds you up by preventing wrong work.

---

**Last Updated:** 2026-01-05
**Version:** 1.0
**Status:** Mandatory

**Remember: 4 minutes of planning prevents 4 hours of rework! 🎯**
