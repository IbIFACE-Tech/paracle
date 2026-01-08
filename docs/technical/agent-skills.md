# Agent Skills System

## Overview

The Agent Skills System enables runtime loading and injection of specialized knowledge into agents. Skills are defined in `.parac/agents/skills/` and can be dynamically loaded during agent execution.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   .parac/agents/skills/                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │paracle-dev/  │  │api-dev/      │  │testing-qa/   │      │
│  │ SKILL.md     │  │ SKILL.md     │  │ SKILL.md     │      │
│  │ assets/      │  │ scripts/     │  │ references/  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                    SkillLoader
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                     Agent Execution                         │
│                                                             │
│  1. AgentCoordinator.execute_agent()                       │
│  2. Load skills for agent (from SKILL_ASSIGNMENTS.md)     │
│  3. SkillInjector enhances system prompt                   │
│  4. Execute with enhanced prompt + skill context           │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. SkillLoader

**Purpose**: Load skills from `.parac/agents/skills/` directory

**Features**:

- Skill discovery
- Lazy loading with caching
- Agent-to-skill mapping (from `SKILL_ASSIGNMENTS.md`)
- Asset/script/reference loading

**Usage**:

```python
from paracle_orchestration import SkillLoader

loader = SkillLoader()
skills = loader.discover_skills()  # List all available
skill = loader.load_skill("paracle-development")  # Load specific
coder_skills = loader.load_agent_skills("coder")  # Load by agent
```

### 2. SkillInjector

**Purpose**: Inject skill knowledge into agent system prompts

**Injection Modes**:

- **full**: Complete skill content (verbose, maximum context)
- **summary**: Descriptions only (balanced, recommended)
- **references**: Reference docs only (focused)
- **minimal**: Just skill names (lightweight)

**Usage**:

```python
from paracle_orchestration import SkillInjector

injector = SkillInjector(injection_mode="full")
enhanced = injector.inject_skills(original_prompt, skills)
skill_context = injector.create_skill_context(skills)
```

### 3. AgentCoordinator Integration

**Purpose**: Automatically load and inject skills during execution

**Features**:

- Optional skill loading (enable/disable)
- Configurable injection mode
- Per-execution control (`load_skills` parameter)
- Skill metadata in results

**Usage**:

```python
from paracle_orchestration import AgentCoordinator

coordinator = AgentCoordinator(
    agent_factory=factory,
    enable_skills=True,              # Enable skill system
    skill_injection_mode="full",     # Injection mode
    parac_dir=".parac",              # Skills directory
)

result = await coordinator.execute_agent(
    agent=agent,
    inputs={"task": "..."},
    load_skills=True,                # Load skills for this execution
)

print(result["metadata"]["skills_loaded"])  # Number of skills
print(result["metadata"]["skill_ids"])      # Loaded skill IDs
```

### 4. AgentSpec Enhancement

**Purpose**: Track skills assigned to agents

**New Field**:

```python
from paracle_domain.models import AgentSpec

agent_spec = AgentSpec(
    name="coder",
    skills=[                         # NEW: Explicit skill assignment
        "paracle-development",
        "api-development",
        "testing-qa",
    ],
    # ... other fields
)
```

**Note**: Skills can be specified in AgentSpec OR loaded from SKILL_ASSIGNMENTS.md

## Skill Structure

### Directory Layout

```
.parac/agents/skills/
├── paracle-development/
│   ├── SKILL.md              # Main skill content (required)
│   ├── assets/               # Templates, examples (optional)
│   │   └── template.py
│   ├── scripts/              # Executable scripts (optional)
│   │   └── helper.sh
│   └── references/           # Reference docs (optional)
│       └── api-guide.md
├── api-development/
│   └── SKILL.md
└── testing-qa/
    └── SKILL.md
```

### SKILL.md Format

```markdown
# Skill Name

## Description
Brief description of what this skill provides.

## Capabilities
- Capability 1
- Capability 2

## Best Practices
1. Practice 1
2. Practice 2

## Examples
```python
# Code example
```

## References

- Link 1
- Link 2

```

## Configuration

### Environment Variables

```bash
# Optional: Custom .parac directory
export PARACLE_PARAC_DIR="/custom/path/.parac"
```

### Coordinator Initialization

```python
coordinator = AgentCoordinator(
    agent_factory=factory,
    enable_skills=True,              # Default: True
    skill_injection_mode="full",     # Default: "full"
    parac_dir=None,                  # Default: ./.parac
)
```

### Execution Options

```python
# Load skills for this execution
result = await coordinator.execute_agent(
    agent, inputs, load_skills=True
)

# Skip skills for this execution
result = await coordinator.execute_agent(
    agent, inputs, load_skills=False
)
```

## Examples

### Example 1: Basic Usage

```python
from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_orchestration import AgentCoordinator

# Create agent
agent_spec = AgentSpec(
    name="coder",
    role="Code implementation",
    system_prompt="You are a skilled programmer.",
    provider="openai",
    model="gpt-4",
)

# Create coordinator with skills
factory = AgentFactory()
coordinator = AgentCoordinator(
    agent_factory=factory,
    enable_skills=True,
    skill_injection_mode="full",
)

# Execute with skills
agent = factory.create(agent_spec)
result = await coordinator.execute_agent(
    agent=agent,
    inputs={"task": "Implement REST API endpoint"},
)

print(f"Skills loaded: {result['metadata']['skills_loaded']}")
```

### Example 2: Custom Skill Discovery

```python
from paracle_orchestration import SkillLoader

loader = SkillLoader()

# Discover all skills
all_skills = loader.discover_skills()
print(f"Available skills: {all_skills}")

# Load skills for specific agent
coder_skills = loader.load_agent_skills("coder")
for skill in coder_skills:
    print(f"- {skill.name}: {skill.description}")

# Load specific skill
skill = loader.load_skill("paracle-development")
if skill:
    print(f"Content: {skill.content[:200]}...")
```

### Example 3: Different Injection Modes

```python
modes = ["full", "summary", "references", "minimal"]

for mode in modes:
    coordinator = AgentCoordinator(
        agent_factory=factory,
        enable_skills=True,
        skill_injection_mode=mode,
    )

    result = await coordinator.execute_agent(agent, inputs)
    print(f"{mode}: {result['metadata']['skills_loaded']} skills")
```

### Example 4: Conditional Skill Loading

```python
# Load skills only for complex tasks
if task_complexity == "high":
    result = await coordinator.execute_agent(
        agent, inputs, load_skills=True
    )
else:
    result = await coordinator.execute_agent(
        agent, inputs, load_skills=False
    )
```

## Performance Considerations

### Caching

Skills are cached after first load to avoid repeated file I/O:

```python
loader = SkillLoader()
skill1 = loader.load_skill("api-development")  # Loads from disk
skill2 = loader.load_skill("api-development")  # Returns cached
# skill1 is skill2 → True
```

### Injection Mode Impact

| Mode       | Prompt Size | Context Usage | Recommended For               |
| ---------- | ----------- | ------------- | ----------------------------- |
| full       | Large       | High          | Complex tasks, new agents     |
| summary    | Medium      | Medium        | General usage (default)       |
| references | Medium      | Medium        | Documentation tasks           |
| minimal    | Small       | Low           | Simple tasks, limited context |

### Best Practices

1. **Use "summary" mode by default** - Best balance
2. **Cache skill loaders** - Reuse across multiple executions
3. **Load skills selectively** - Use `load_skills=False` for simple tasks
4. **Keep SKILL.md focused** - Avoid overly verbose content
5. **Structure skills logically** - One skill per domain/capability

## Troubleshooting

### Skills Not Loading

**Problem**: Skills not appearing in results

**Solutions**:

1. Check `.parac/agents/skills/` directory exists
2. Verify `SKILL.md` files exist in skill directories
3. Check `SKILL_ASSIGNMENTS.md` has correct mappings
4. Ensure `enable_skills=True` in coordinator
5. Check logs for warnings

### Empty Skill List

**Problem**: `load_agent_skills()` returns empty list

**Solutions**:

1. Verify agent name matches SKILL_ASSIGNMENTS.md
2. Check skill directory names match assigned skill IDs
3. Review SKILL_ASSIGNMENTS.md format
4. Test with `loader.discover_skills()` first

### Memory Issues

**Problem**: High memory usage with skills

**Solutions**:

1. Use "summary" or "minimal" injection mode
2. Clear cache periodically: `loader.clear_cache()`
3. Reduce number of assigned skills
4. Optimize SKILL.md content length

### Prompt Too Long

**Problem**: System prompt exceeds model limits

**Solutions**:

1. Switch to "summary" or "minimal" mode
2. Reduce number of skills per agent
3. Truncate SKILL.md content
4. Use references mode for documentation-heavy skills

## Testing

### Unit Tests

```bash
# Run skill system tests
pytest tests/unit/test_skills.py -v

# Test with integration
pytest tests/unit/test_skills.py::TestSkillIntegration -v
```

### Manual Testing

```python
# Test skill discovery
python -c "
from paracle_orchestration import SkillLoader
loader = SkillLoader()
print(loader.discover_skills())
"

# Test skill loading
python -c "
from paracle_orchestration import SkillLoader
loader = SkillLoader()
skills = loader.load_agent_skills('coder')
print(f'Loaded {len(skills)} skills')
"

# Run example
python examples/14_agent_skills.py
```

## Migration Guide

### Updating Existing Agents

**Before** (no skills):

```python
coordinator = AgentCoordinator(agent_factory=factory)
result = await coordinator.execute_agent(agent, inputs)
```

**After** (with skills):

```python
coordinator = AgentCoordinator(
    agent_factory=factory,
    enable_skills=True,              # Enable skills
    skill_injection_mode="summary",  # Choose mode
)
result = await coordinator.execute_agent(agent, inputs)
# result["metadata"]["skills_loaded"] now available
```

### Adding Skills to AgentSpec

**Optional** - skills can be loaded from SKILL_ASSIGNMENTS.md:

```python
agent_spec = AgentSpec(
    name="coder",
    skills=["paracle-development", "api-development"],  # NEW
    # ... other fields
)
```

### Gradual Adoption

1. **Phase 1**: Enable skills but use minimal mode
2. **Phase 2**: Test with summary mode on non-critical agents
3. **Phase 3**: Use full mode for complex agents
4. **Phase 4**: Create custom skills for your domain

## API Reference

### SkillLoader

```python
class SkillLoader:
    def __init__(self, parac_dir: Path | None = None)
    def discover_skills(self) -> list[str]
    def load_skill(self, skill_id: str) -> Skill | None
    def load_agent_skills(self, agent_name: str) -> list[Skill]
    def get_agent_skill_ids(self, agent_name: str) -> list[str]
    def clear_cache(self) -> None
```

### SkillInjector

```python
class SkillInjector:
    def __init__(self, injection_mode: str = "full")
    def inject_skills(
        self,
        system_prompt: str | None,
        skills: list[Skill]
    ) -> str
    def create_skill_context(self, skills: list[Skill]) -> dict
```

### Skill

```python
class Skill:
    skill_id: str
    name: str
    description: str
    content: str
    assets: dict[str, str]
    scripts: dict[str, str]
    references: dict[str, str]

    def to_dict(self) -> dict
```

## Related Documentation

- [Agent Specifications](agent-execution-quickref.md)
- [Orchestration Guide](../examples/README.md#orchestration)
- [SKILL_ASSIGNMENTS.md](../.parac/agents/SKILL_ASSIGNMENTS.md)
- [Example: Agent Skills](../examples/14_agent_skills.py)

---

**Status**: ✅ Implemented (Phase 5+)
**Version**: 0.0.1
**Last Updated**: 2026-01-06
