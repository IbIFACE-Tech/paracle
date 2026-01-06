# Agent Inheritance - Real-World Example

## Overview

This document explains Paracle's unique **Agent Inheritance** feature through a practical example: building a team of specialized code reviewers.

## What is Agent Inheritance?

Agent Inheritance allows agents to inherit properties from parent agents, similar to class inheritance in object-oriented programming. This enables:

- **DRY Principle**: Define common behavior once in a base agent
- **Progressive Specialization**: Each level adds domain expertise
- **Easy Maintenance**: Update base agent affects all children
- **Type Safety**: Pydantic validation at every level
- **Flexible Overrides**: Children can override any parent property

## The Example: Code Reviewer Hierarchy

### Architecture

```
base-code-reviewer (General Reviewer)
    ↓ inherits & adds
python-code-reviewer (Python Specialist)
    ↓ inherits & adds
fastapi-code-reviewer (API Specialist)
    ↓ inherits & adds
security-code-reviewer (Security Specialist)
```

### Level 1: Base Code Reviewer

```python
base_spec = AgentSpec(
    name="base-code-reviewer",
    description="General code reviewer for any language",
    provider="openai",
    model="gpt-4",
    temperature=0.3,
    system_prompt="You are an experienced code reviewer.",
    tools=["read_file", "grep_search"],
    skills=["code-review"],
    metadata={
        "role": "reviewer",
        "experience_level": "senior",
    }
)
```

**Purpose**: Foundation for all code reviewers
- **Tools**: Basic file reading and search
- **Skills**: General code review
- **Temperature**: 0.3 (balanced)

### Level 2: Python Specialist

```python
python_spec = AgentSpec(
    name="python-code-reviewer",
    description="Python code reviewer",
    parent="base-code-reviewer",  # 🔥 INHERITANCE!
    provider="openai",
    model="gpt-4",
    temperature=0.2,  # Stricter
    system_prompt="You are a Python expert code reviewer.",
    tools=["run_python_linter", "check_type_hints"],
    skills=["python-best-practices", "typing"],
    metadata={
        "language": "python",
        "pep8_strict": True,
    }
)
```

**Inherits from**: base-code-reviewer
- **Inherited**: read_file, grep_search tools + code-review skill
- **Adds**: Python-specific tools and skills
- **Overrides**: Temperature (0.2), system prompt
- **Total**: 4 tools, 3 skills

### Level 3: FastAPI Specialist

```python
fastapi_spec = AgentSpec(
    name="fastapi-code-reviewer",
    description="FastAPI/REST API code reviewer",
    parent="python-code-reviewer",  # 🔥 MULTI-LEVEL INHERITANCE!
    provider="openai",
    model="gpt-4-turbo",  # Upgraded model
    temperature=0.25,
    system_prompt="You are a FastAPI and REST API expert.",
    tools=["validate_openapi", "check_api_security"],
    skills=["api-design", "fastapi", "rest-patterns"],
    metadata={
        "framework": "fastapi",
        "api_version": "v1",
    }
)
```

**Inherits from**: python-code-reviewer (which inherits from base)
- **Inherited**: All tools and skills from base + Python
- **Adds**: FastAPI/API specific capabilities
- **Overrides**: Model (gpt-4-turbo), temperature
- **Total**: 6 tools, 6 skills

### Level 4: Security Specialist

```python
security_spec = AgentSpec(
    name="security-code-reviewer",
    description="Security-focused code reviewer",
    parent="fastapi-code-reviewer",  # 🔥 3-LEVEL INHERITANCE CHAIN!
    provider="openai",
    model="gpt-4-turbo",
    temperature=0.1,  # Strictest for security
    system_prompt="You are a security expert.",
    tools=["scan_vulnerabilities", "check_dependencies", "audit_auth"],
    skills=["security-audit", "owasp", "penetration-testing"],
    metadata={
        "security_level": "high",
        "owasp_version": "2023",
    }
)
```

**Inherits from**: fastapi-code-reviewer (3-level chain)
- **Inherited**: All capabilities from base + Python + FastAPI
- **Adds**: Security-specific tools and skills
- **Overrides**: Temperature (0.1 - strictest)
- **Total**: 9 tools, 9 skills

## How Inheritance Works

### Property Merging Rules

| Property        | Merge Strategy                                                     | Example                                 |
| --------------- | ------------------------------------------------------------------ | --------------------------------------- |
| `tools`         | **Additive** - Child tools added to parent tools (no duplicates)   | base: [A, B] + child: [C] = [A, B, C]   |
| `skills`        | **Additive** - Child skills added to parent skills (no duplicates) | base: [X] + child: [Y, Z] = [X, Y, Z]   |
| `metadata`      | **Merge** - Child keys override parent keys                        | base: {a:1} + child: {b:2} = {a:1, b:2} |
| `config`        | **Merge** - Child keys override parent keys                        | Same as metadata                        |
| `temperature`   | **Override** - Child value replaces parent                         | base: 0.3 → child: 0.2                  |
| `model`         | **Override** - Child value replaces parent                         | base: gpt-4 → child: gpt-4-turbo        |
| `system_prompt` | **Override** - Child value replaces parent                         | More specialized at each level          |

### Temperature Evolution

Notice how temperature becomes stricter at each specialization level:

```
Base:     0.3  (balanced)
Python:   0.2  (stricter - Python standards)
FastAPI:  0.25 (slightly relaxed for API flexibility)
Security: 0.1  (strictest - security critical)
```

### Tool Accumulation

```
Level 1 (Base):     2 tools  [read_file, grep_search]
Level 2 (Python):   4 tools  + [run_python_linter, check_type_hints]
Level 3 (FastAPI):  6 tools  + [validate_openapi, check_api_security]
Level 4 (Security): 9 tools  + [scan_vulnerabilities, check_dependencies, audit_auth]
```

### Skill Accumulation

```
Level 1 (Base):     1 skill  [code-review]
Level 2 (Python):   3 skills + [python-best-practices, typing]
Level 3 (FastAPI):  6 skills + [api-design, fastapi, rest-patterns]
Level 4 (Security): 9 skills + [security-audit, owasp, penetration-testing]
```

## Usage

### Running the Example

```bash
cd paracle-lite
uv run python examples/real_world_inheritance.py
```

Output shows:
- Creation of each agent
- Inheritance chain
- Tool/skill accumulation
- Property overrides
- Verification tests

### Running the Tests

```bash
# All tests
uv run pytest tests/integration/test_real_world_inheritance.py -v

# Specific test
uv run pytest tests/integration/test_real_world_inheritance.py::TestRealWorldInheritance::test_security_three_level_inheritance -v
```

## Implementation Details

### Step 1: Create Repository and Factory

```python
from paracle_domain.factory import AgentFactory
from paracle_store import AgentRepository

# Initialize
repo = AgentRepository()
factory = AgentFactory(spec_provider=repo.get_spec)
```

### Step 2: Register and Create Agents

```python
# Register parent spec first
repo.register_spec(base_spec)
base_agent = factory.create(base_spec)

# Then register child (parent must exist)
repo.register_spec(python_spec)
python_agent = factory.create(python_spec)

# Factory resolves inheritance automatically
effective_spec = python_agent.get_effective_spec()
# effective_spec now has merged tools, skills, metadata
```

### Step 3: Access Effective Spec

```python
# Get the resolved spec (after inheritance resolution)
spec = agent.get_effective_spec()

# Access accumulated tools
print(spec.tools)  # All tools from parent + child

# Access accumulated skills
print(spec.skills)  # All skills from parent + child

# Overridden values
print(spec.temperature)  # Child's value
print(spec.model)  # Child's value
```

## Benefits Demonstrated

### 1. DRY Principle

Update base agent, all children inherit the change:

```python
# Update base agent
base_spec.tools.append("new_common_tool")
repo.register_spec(base_spec)

# New child automatically gets the tool
new_child = factory.create(child_spec)
assert "new_common_tool" in new_child.get_effective_spec().tools
```

### 2. Progressive Specialization

Each level adds domain expertise:
- Base: General review
- Python: + Python standards
- FastAPI: + API design
- Security: + Security audits

### 3. Practical Team Structure

Mirrors real-world team organization:
- Junior reviewers use base agent
- Python devs use Python reviewer
- API team uses FastAPI reviewer
- Security team uses security reviewer

Each has appropriate tools and strictness level.

## Validation & Safety

### Max Depth Limit

```python
# Default: Max 5 levels, warning at 3+
factory = AgentFactory(
    spec_provider=repo.get_spec,
    max_inheritance_depth=5,
    warn_depth=3
)
```

### Circular Dependency Detection

```python
# This raises CircularInheritanceError
agent_a.parent = "agent-b"
agent_b.parent = "agent-a"
factory.create(agent_a)  # Error!
```

### No Duplicate Tools/Skills

Inheritance resolution automatically deduplicates:

```python
# Even if parent and child both specify "read_file"
# It appears only once in effective spec
assert effective_spec.tools.count("read_file") == 1
```

## Comparison with Other Frameworks

| Feature            | Paracle    | LangChain | LlamaIndex | AutoGen |
| ------------------ | ---------- | --------- | ---------- | ------- |
| Agent Inheritance  | ✅ Yes      | ❌ No      | ❌ No       | ❌ No    |
| Multi-level        | ✅ Yes      | ❌ No      | ❌ No       | ❌ No    |
| Property Merging   | ✅ Smart    | -         | -          | -       |
| Type Safety        | ✅ Pydantic | Partial   | Partial    | Partial |
| Circular Detection | ✅ Yes      | -         | -          | -       |

**Paracle is the ONLY framework with agent inheritance!**

## Advanced Patterns

### Pattern 1: Role Hierarchy

```
base-agent (Foundation)
  ├─ developer-agent (Dev capabilities)
  │   ├─ frontend-dev (React, Vue)
  │   └─ backend-dev (APIs, DB)
  └─ qa-agent (Testing capabilities)
      ├─ unit-tester
      └─ integration-tester
```

### Pattern 2: Domain Specialization

```
base-data-analyst (Data skills)
  ├─ marketing-analyst (Marketing metrics)
  ├─ finance-analyst (Financial data)
  └─ product-analyst (Product metrics)
```

### Pattern 3: Skill Progression

```
junior-dev (temp: 0.7, basic tools)
  ↓
mid-dev (temp: 0.5, + advanced tools)
  ↓
senior-dev (temp: 0.3, + architecture skills)
  ↓
architect (temp: 0.2, + system design)
```

## Best Practices

### 1. Design Shallow Hierarchies

✅ **Good**: 2-3 levels
```
base → specialist → expert
```

❌ **Avoid**: Deep hierarchies (5+ levels)
```
base → l1 → l2 → l3 → l4 → l5 → l6  # Too complex!
```

### 2. Use Meaningful Names

✅ **Good**: Descriptive, hierarchical
```
base-reviewer → python-reviewer → security-reviewer
```

❌ **Avoid**: Generic or cryptic
```
agent1 → agent2 → agent3
```

### 3. Override Sparingly

Only override what changes:
```python
# Good - only override what's different
child = AgentSpec(
    name="child",
    parent="base",
    temperature=0.2,  # Just this
)

# Avoid - repeating everything
child = AgentSpec(
    name="child",
    parent="base",
    temperature=0.2,
    provider="openai",  # Already in parent
    model="gpt-4",      # Already in parent
    tools=["tool1"],    # Should merge, not replace
)
```

### 4. Register Parents First

```python
# Correct order
repo.register_spec(base_spec)
repo.register_spec(child_spec)  # Parent exists

# Wrong - raises ParentNotFoundError
repo.register_spec(child_spec)  # Parent doesn't exist yet!
```

## Testing

The example includes comprehensive tests covering:

- ✅ Single-level inheritance
- ✅ Multi-level inheritance (3 levels)
- ✅ Tool accumulation
- ✅ Skill accumulation
- ✅ Property overrides
- ✅ Metadata merging
- ✅ No duplicates
- ✅ Temperature cascade
- ✅ Model upgrades
- ✅ System prompt specialization
- ✅ Practical usage scenarios
- ✅ DRY principle validation

Run all tests:
```bash
uv run pytest tests/integration/test_real_world_inheritance.py -v
```

## Files

- **Example**: `examples/real_world_inheritance.py`
- **Tests**: `tests/integration/test_real_world_inheritance.py`
- **Implementation**: `packages/paracle_domain/inheritance.py`
- **Factory**: `packages/paracle_domain/factory.py`
- **Models**: `packages/paracle_domain/models.py`

## Related Documentation

- [Agent Inheritance Design](agent-inheritance-design.md) - Technical design
- [Agent Factory](agent-factory.md) - Factory pattern
- [Agent Models](agent-models.md) - Core models
- [Getting Started](getting-started.md) - Quick start guide

---

**This unique feature makes Paracle stand out from all other multi-agent frameworks!** 🚀
