# Agent Inheritance with .parac/agents/

## Overview

This guide shows how to use agent inheritance with agents defined in `.parac/agents/`, demonstrating how to create specialized agents that inherit from the base agents used to build Paracle itself.

## Bug Fix

**Important**: We discovered and fixed a bug in the inheritance system where **skills were not being merged** during inheritance resolution. This has been fixed in `packages/paracle_domain/inheritance.py`.

### What Was Fixed

```python
# Before (bug):
merged_tools = list(base.tools)
# Skills were missing!
merged_metadata = dict(base.metadata)

# After (fixed):
merged_tools = list(base.tools)
merged_skills = list(base.skills)  # ← Now skills are merged!
merged_metadata = dict(base.metadata)
```

The fix ensures that:
- ✅ Skills accumulate through inheritance chains
- ✅ No duplicates (like tools)
- ✅ Child skills are added to parent skills

## Basic Pattern

### 1. Load Base Agent from .parac/

```python
from pathlib import Path
from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_store import AgentRepository

# Setup
repo = AgentRepository()
factory = AgentFactory(spec_provider=repo.get_spec)

# Create base reviewer (from .parac/agents/specs/reviewer.md)
base_reviewer = AgentSpec(
    name="reviewer",
    description="Code reviewer ensuring quality and best practices",
    provider="openai",
    model="gpt-4",
    temperature=0.3,
    system_prompt="You are a code reviewer ensuring quality and best practices.",
    tools=["static_analysis", "security_scan", "code_review"],
    skills=["code-review", "quality-assurance", "security-hardening"],
    metadata={
        "role": "code_review",
        "source": ".parac/agents/specs/reviewer.md",
    }
)

repo.register_spec(base_reviewer)
```

### 2. Create Specialized Child Agent

```python
# Create security-focused reviewer (inherits from reviewer)
security_reviewer = AgentSpec(
    name="security-reviewer",
    description="Security-focused code reviewer",
    parent="reviewer",  # 🔥 Inherits from base!
    provider="openai",
    model="gpt-4",
    temperature=0.2,  # Stricter
    system_prompt="You are a security expert reviewing code for vulnerabilities.",
    tools=[
        "vulnerability_scanner",
        "dependency_checker",
        "secret_detector",
    ],  # Additional security tools
    skills=[
        "owasp-top-10",
        "penetration-testing",
        "threat-modeling",
    ],  # Additional security skills
    metadata={
        "focus": "security",
        "owasp_version": "2023",
    }
)

repo.register_spec(security_reviewer)
agent = factory.create(security_reviewer)
effective = agent.get_effective_spec()
```

### 3. Verify Inheritance

```python
# Check inherited tools
assert "static_analysis" in effective.tools  # From base
assert "vulnerability_scanner" in effective.tools  # Own
assert len(effective.tools) == 6  # 3 base + 3 own

# Check inherited skills
assert "code-review" in effective.skills  # From base
assert "owasp-top-10" in effective.skills  # Own
assert len(effective.skills) == 6  # 3 base + 3 own

# Check metadata merging
assert effective.metadata["role"] == "code_review"  # From base
assert effective.metadata["focus"] == "security"  # Own
```

## Multi-Level Inheritance

### Create Grandchild Agent

```python
# Level 1: Base reviewer (already created)
# Level 2: Security reviewer (already created)

# Level 3: Python-specific security reviewer
python_security_reviewer = AgentSpec(
    name="python-security-reviewer",
    description="Python-specific security reviewer",
    parent="security-reviewer",  # 🔥 Inherits from security reviewer!
    provider="openai",
    model="gpt-4-turbo",
    temperature=0.15,  # Even stricter
    system_prompt="You are a Python security expert...",
    tools=["bandit", "safety"],  # Python-specific tools
    skills=["python-security", "pickle-safety"],  # Python-specific skills
    metadata={"language": "python"}
)

repo.register_spec(python_security_reviewer)
agent = factory.create(python_security_reviewer)
effective = agent.get_effective_spec()

# Inherits through 2 levels:
# - From grandparent (reviewer): static_analysis, code-review
# - From parent (security): vulnerability_scanner, owasp-top-10
# - Own: bandit, python-security

assert len(effective.tools) == 7  # 3 + 2 + 2
assert len(effective.skills) == 7  # 3 + 2 + 2
```

## Inheritance Hierarchy Example

```
reviewer (base from .parac/agents/specs/reviewer.md)
├── security-reviewer
│   └── python-security-reviewer (2-level inheritance)
└── performance-reviewer

Tools accumulation:
- reviewer:                  3 tools
- security-reviewer:         6 tools (3 + 3)
- python-security-reviewer:  7 tools (3 + 2 + 2)
- performance-reviewer:      6 tools (3 + 3)

Skills accumulation:
- reviewer:                  3 skills
- security-reviewer:         6 skills (3 + 3)
- python-security-reviewer:  7 skills (3 + 2 + 2)
- performance-reviewer:      6 skills (3 + 3)
```

## Property Inheritance Rules

| Property          | Inheritance Behavior             | Example                                    |
| ----------------- | -------------------------------- | ------------------------------------------ |
| **tools**         | ✅ Additive (no duplicates)       | Base: [A,B] + Child: [C] = [A,B,C]         |
| **skills**        | ✅ Additive (no duplicates)       | Base: [X,Y] + Child: [Z] = [X,Y,Z]         |
| **metadata**      | ✅ Merged (child overrides)       | Base: {a:1} + Child: {a:2,b:3} = {a:2,b:3} |
| **config**        | ✅ Merged (child overrides)       | Same as metadata                           |
| **temperature**   | ⚠️ Child overrides (if different) | Base: 0.3 → Child: 0.2                     |
| **model**         | ⚠️ Child overrides                | Base: gpt-4 → Child: gpt-4-turbo           |
| **provider**      | ⚠️ Child overrides                | Base: openai → Child: anthropic            |
| **system_prompt** | ⚠️ Child overrides                | Completely replaced                        |

## Complete Working Example

See [`examples/parac_agents_inheritance.py`](../examples/parac_agents_inheritance.py) for a complete example that:

1. Loads base reviewer from `.parac/agents/specs/reviewer.md`
2. Creates security-reviewer (child)
3. Creates performance-reviewer (sibling)
4. Creates python-security-reviewer (grandchild)
5. Demonstrates tool/skill accumulation
6. Shows temperature specialization
7. Validates all inheritance rules

## Tests

See [`tests/integration/test_parac_agents_inheritance.py`](../tests/integration/test_parac_agents_inheritance.py) for comprehensive tests covering:

- Single-level inheritance
- Multi-level inheritance (2+ levels)
- Sibling specializations
- Property overrides
- Metadata merging
- No duplicates
- Validation

**Run tests:**

```bash
uv run pytest tests/integration/test_parac_agents_inheritance.py -v
```

## Required Fields

**Important**: When creating child agents, you must still specify required fields:

```python
# ❌ This will fail validation:
child = AgentSpec(
    name="child",
    parent="parent",
    # Missing provider and model!
)

# ✅ This works:
child = AgentSpec(
    name="child",
    parent="parent",
    provider="openai",  # Required
    model="gpt-4",      # Required
)
```

Even though the child inherits from parent, Pydantic validation requires `provider` and `model` to be explicitly set.

## Benefits

✅ **DRY Principle**: Define base capabilities once in `.parac/agents/specs/`
✅ **Specialization**: Create focused agents by adding specific tools/skills
✅ **Maintenance**: Update base agent → all children inherit changes
✅ **Type Safety**: Pydantic validation ensures correctness
✅ **Traceability**: Metadata tracks inheritance source
✅ **Flexibility**: Mix base agents with specialized agents in workflows

## Use Cases

### Security Audit Pipeline

```python
# Use different reviewers for different security aspects
security_reviewer = factory.create("security-reviewer")  # General
python_security = factory.create("python-security-reviewer")  # Python-specific
# Both inherit base review capabilities + add security focus
```

### Performance Analysis

```python
# Base reviewer + performance focus
performance_reviewer = factory.create("performance-reviewer")
# Inherits code review skills + adds profiling/optimization tools
```

### Language-Specific Reviews

```python
# Create specialized reviewers per language
python_reviewer = AgentSpec(parent="coder", language="python", ...)
typescript_reviewer = AgentSpec(parent="coder", language="typescript", ...)
# Both inherit base coding capabilities + add language-specific tools
```

## Integration with Workflows

```python
from paracle_orchestration import Workflow

# Create workflow using inherited agents
workflow = Workflow(
    steps=[
        {"agent": "reviewer", "task": "general_review"},
        {"agent": "security-reviewer", "task": "security_audit"},
        {"agent": "python-security-reviewer", "task": "python_security_check"},
    ]
)
```

## Next Steps

1. ✅ Explore [`examples/parac_agents_inheritance.py`](../examples/parac_agents_inheritance.py)
2. ✅ Run tests: `uv run pytest tests/integration/test_parac_agents_inheritance.py`
3. ✅ Create your own specialized agents from `.parac/agents/` base agents
4. ✅ Integrate with workflows for multi-stage processing

---

**Related Documentation:**

- [Agent Inheritance Example](agent-inheritance-example.md) - Full inheritance guide
- [Agent Discovery](agent-discovery.md) - Finding and loading agents
- [.parac/agents/SKILL_ASSIGNMENTS.md](../.parac/agents/SKILL_ASSIGNMENTS.md) - Skills per agent
- [Workflow Guide](workflow-guide.md) - Using agents in workflows

